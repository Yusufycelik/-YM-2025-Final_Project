from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from app.models import Payment, PaymentStatus, PaymentMethod
from app.schemas import PaymentCreate, PaymentUpdate
from app.utils.rabbitmq import publish_message
import httpx
from app.config import settings


def generate_payment_number() -> str:
    """Benzersiz ödeme numarası oluştur"""
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"


def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payment_by_number(db: Session, payment_number: str):
    return db.query(Payment).filter(Payment.payment_number == payment_number).first()


def get_user_payments(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Payment).filter(Payment.user_id == user_id).offset(skip).limit(limit).all()


async def create_payment(db: Session, payment: PaymentCreate):
    """Ödeme işlemi oluştur"""
    # Ticket bilgilerini ticket-service'den al
    try:
        print(f"[PAYMENT_SERVICE] Fetching ticket {payment.ticket_id} from {settings.TICKET_SERVICE_URL}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.TICKET_SERVICE_URL}/api/v1/tickets/{payment.ticket_id}")
            if response.status_code != 200:
                print(f"[PAYMENT_SERVICE] Ticket service returned status {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ticket not found"
                )
            ticket_data = response.json()
            print(f"[PAYMENT_SERVICE] Successfully fetched ticket data: {ticket_data.get('id')}")
    except httpx.ConnectError as e:
        print(f"[PAYMENT_SERVICE] Connection error to ticket service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ticket service unavailable: {str(e)}"
        )
    except httpx.TimeoutException as e:
        print(f"[PAYMENT_SERVICE] Timeout connecting to ticket service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ticket service timeout: {str(e)}"
        )
    except httpx.RequestError as e:
        print(f"[PAYMENT_SERVICE] Request error to ticket service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ticket service unavailable: {str(e)}"
        )
    except Exception as e:
        print(f"[PAYMENT_SERVICE] Unexpected error fetching ticket: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ticket service error: {str(e)}"
        )
    
    # Bilet durumu kontrolü
    if ticket_data["status"] != "reserved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket is not in reserved status"
        )
    
    # Ödeme oluştur
    payment_number = generate_payment_number()
    db_payment = Payment(
        payment_number=payment_number,
        ticket_id=payment.ticket_id,
        user_id=payment.user_id,
        amount=ticket_data["total_price"],
        currency=payment.currency,
        payment_method=payment.payment_method,
        status=PaymentStatus.PENDING
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Ödeme işlemini simüle et (gerçek uygulamada payment gateway entegrasyonu olur)
    # Kart bilgilerini payment_data'ya ekle
    payment_data = {}
    if hasattr(payment, 'dict'):
        payment_dict = payment.dict()
        payment_data = {
            "card_number": payment_dict.get("card_number"),
            "card_holder_name": payment_dict.get("card_holder_name"),
            "expiry_date": payment_dict.get("expiry_date"),
            "cvv": payment_dict.get("cvv")
        }
    
    await process_payment(db, db_payment.id, payment_data, ticket_data)
    
    return db_payment


async def process_payment(db: Session, payment_id: int, payment_data: Optional[dict] = None, ticket_data: Optional[dict] = None):
    """Ödeme işlemini gerçekleştir (simüle edilmiş)"""
    print(f"[PAYMENT_SERVICE] process_payment called: payment_id={payment_id}, payment_data={payment_data}, ticket_data={ticket_data}")
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        print(f"[PAYMENT_SERVICE] Payment {payment_id} not found!")
        return
    
    # Simüle edilmiş ödeme işlemi
    # Gerçek uygulamada burada payment gateway API çağrısı yapılır
    import random
    import asyncio
    
    # Ödeme işleme süresini simüle et
    await asyncio.sleep(0.5)
    print(f"[PAYMENT_SERVICE] Processing payment {payment_id}...")
    
    # Kart bilgisi kontrolü (simülasyon)
    success = True
    failure_reason = None
    
    if not payment_data or not payment_data.get("card_number"):
        # Kart bilgisi zorunlu
        success = False
        failure_reason = "Card information is required"
    else:
        card_number = payment_data["card_number"].replace(" ", "").replace("-", "")
        
        # Kart numarası uzunluk kontrolü
        if len(card_number) < 13 or len(card_number) > 19:
            success = False
            failure_reason = "Invalid card number length"
        # Son 4 haneyi kontrol et (test senaryoları)
        elif card_number[-4:] == "0000":  # Test için: son 4 hane 0000 ise başarısız
            success = False
            failure_reason = "Card declined by bank"
        elif card_number[-4:] == "1111":  # Test için: son 4 hane 1111 ise yetersiz bakiye
            success = False
            failure_reason = "Insufficient funds"
        else:
            # Geçerli kart - %98 başarı oranı (kart bilgileri doğruysa)
            success = random.random() > 0.02
            if not success:
                failure_reason = "Payment gateway declined the transaction"
    
    if success:
        print(f"[PAYMENT_SERVICE] Payment {payment_id} SUCCESSFUL!")
        db_payment.status = PaymentStatus.COMPLETED
        db_payment.completed_at = datetime.utcnow()
        db_payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        db.commit()
        db.refresh(db_payment)
        
        # Ticket service'e ödeme tamamlandı mesajı gönder
        print(f"[PAYMENT_SERVICE] Sending message to tickets/payment.completed...")
        publish_message(
            exchange="tickets",
            routing_key="payment.completed",
            message={
                "payment_id": db_payment.id,
                "ticket_id": db_payment.ticket_id
            }
        )
        
        # Notification service'e bildirim gönder (ticket bilgileriyle birlikte)
        notification_message = {
            "user_id": db_payment.user_id,
            "payment_id": db_payment.id,
            "payment_number": db_payment.payment_number,
            "amount": db_payment.amount,
            "ticket_id": db_payment.ticket_id
        }
        
        # Ticket bilgilerini ekle (varsa)
        if ticket_data:
            notification_message.update({
                "ticket_number": ticket_data.get("ticket_number"),
                "event_id": ticket_data.get("event_id"),
                "quantity": ticket_data.get("quantity"),
                "total_price": ticket_data.get("total_price")
            })
        
        print(f"[PAYMENT_SERVICE] Sending notification message: {notification_message}")
        publish_message(
            exchange="notifications",
            routing_key="payment.completed",
            message=notification_message
        )
        print(f"[PAYMENT_SERVICE] Notification message sent successfully!")
    else:
        print(f"[PAYMENT_SERVICE] Payment {payment_id} FAILED: {failure_reason}")
        db_payment.status = PaymentStatus.FAILED
        db_payment.failure_reason = failure_reason or "Payment gateway declined the transaction"
        
        # Ödeme başarısız olduğunda bilet'i iptal et
        try:
            async with httpx.AsyncClient() as client:
                # Ticket service'e bilet iptali mesajı gönder
                await client.post(
                    f"{settings.TICKET_SERVICE_URL}/api/v1/tickets/{db_payment.ticket_id}/cancel",
                    timeout=5.0
                )
        except httpx.RequestError:
            # Ticket service'e erişilemezse RabbitMQ üzerinden mesaj gönder
            publish_message(
                exchange="tickets",
                routing_key="payment.failed",
                message={
                    "ticket_id": db_payment.ticket_id,
                    "payment_id": db_payment.id
                }
            )
        
        # Notification service'e hata bildirimi gönder
        publish_message(
            exchange="notifications",
            routing_key="payment.failed",
            message={
                "user_id": db_payment.user_id,
                "payment_id": db_payment.id,
                "ticket_id": db_payment.ticket_id,
                "reason": db_payment.failure_reason
            }
        )
    
    db.commit()
    db.refresh(db_payment)
    return db_payment


def update_payment(db: Session, payment_id: int, payment_update: PaymentUpdate):
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    update_data = payment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payment, field, value)
    
    if payment_update.status == PaymentStatus.COMPLETED and not db_payment.completed_at:
        db_payment.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

