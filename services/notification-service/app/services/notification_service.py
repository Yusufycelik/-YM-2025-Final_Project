from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Notification, NotificationType, NotificationStatus
from app.schemas import NotificationCreate
from app.database import SessionLocal
from app.utils.rabbitmq import consume_messages
import json
import pika
import logging

# Logger oluştur
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Console handler ekle
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[NOTIFICATION] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_notification(db: Session, notification: NotificationCreate):
    """Bildirim kaydı oluştur"""
    db_notification = Notification(
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        subject=notification.subject,
        message=notification.message,
        status=NotificationStatus.PENDING
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def send_notification(db: Session, notification_id: int):
    """Bildirim gönder (simüle edilmiş)"""
    # Gerçek uygulamada burada email/SMS servisi entegrasyonu olur
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        return None
    
    logger.info(f"Sending {notification.notification_type} to user {notification.user_id}")
    logger.info(f"Subject: {notification.subject}")
    logger.info(f"Message: {notification.message}")
    
    # Simüle edilmiş gönderim
    notification.status = NotificationStatus.SENT
    notification.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    
    return notification


def handle_ticket_reserved(ch, method, properties, body):
    """Bilet rezervasyonu bildirimi"""
    try:
        message = json.loads(body)
        db = SessionLocal()
        try:
            notification = Notification(
                user_id=message["user_id"],
                notification_type=NotificationType.EMAIL,
                subject="Bilet Rezervasyonu Onaylandı",
                message=f"Bilet numaranız: {message['ticket_number']}\n"
                        f"Etkinlik ID: {message['event_id']}\n"
                        f"Adet: {message['quantity']}\n"
                        f"Toplam Tutar: {message['total_price']} TRY\n\n"
                        f"Ödeme için lütfen bilet detaylarınızı kontrol edin.",
                status=NotificationStatus.PENDING
            )
            db.add(notification)
            db.commit()
            send_notification(notification)
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling ticket reserved: {e}")


def handle_payment_completed(ch, method, properties, body):
    """Ödeme tamamlandı bildirimi"""
    try:
        message = json.loads(body)
        logger.info(f"Received payment.completed message: {message}")
        db = SessionLocal()
        try:
            # Bilet bilgilerini mesajdan al
            ticket_number = message.get('ticket_number', f"Bilet #{message.get('ticket_id', 'N/A')}")
            quantity = message.get('quantity', 1)
            total_price = message.get('total_price', message.get('amount', 0))
            
            notification = Notification(
                user_id=message["user_id"],
                notification_type=NotificationType.EMAIL,
                subject="Bilet Satın Alma Başarılı",
                message=f"Bilet numaranız: {ticket_number}\n"
                        f"Ödeme numaranız: {message['payment_number']}\n"
                        f"Etkinlik ID: {message.get('event_id', 'N/A')}\n"
                        f"Adet: {quantity}\n"
                        f"Toplam Tutar: {total_price} TRY\n\n"
                        f"Biletiniz onaylandı. Etkinlik gününde bilet numaranızı yanınızda bulundurun.",
                status=NotificationStatus.PENDING
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Bildirimi gönder (aynı session ile)
            logger.info(f"Sending notification for payment {message.get('payment_id')}...")
            send_notification(db, notification.id)
            logger.info("Notification sent successfully!")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error handling payment completed: {e}", exc_info=True)


def handle_payment_failed(ch, method, properties, body):
    """Ödeme başarısız bildirimi"""
    try:
        message = json.loads(body)
        print(f"[NOTIFICATION] Received payment.failed message: {message}")
        db = SessionLocal()
        try:
            notification = Notification(
                user_id=message["user_id"],
                notification_type=NotificationType.EMAIL,
                subject="Ödeme Başarısız",
                message=f"Bilet ID: {message['ticket_id']}\n"
                        f"Sebep: {message.get('reason', 'Bilinmeyen hata')}\n\n"
                        f"Lütfen ödeme bilgilerinizi kontrol edip tekrar deneyin.",
                status=NotificationStatus.PENDING
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Bildirimi gönder (aynı session ile)
            send_notification(db, notification.id)
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling payment failed: {e}")
        import traceback
        traceback.print_exc()


def start_consumers():
    """RabbitMQ consumer'ları başlat"""
    import threading
    print("Starting notification consumers...")
    
    # NOT: Ticket reserved consumer kaldırıldı çünkü:
    # - Rezervasyon yapıldığında bildirim göndermiyoruz
    # - Sadece ödeme başarılı olduğunda bildirim gönderiyoruz
    # - Bu sayede kullanıcıya gereksiz bildirim gitmiyor
    
    # Payment completed consumer (ayrı thread'de)
    def start_payment_completed_consumer():
        try:
            print("[NOTIFICATION_SERVICE] Starting payment.completed consumer thread...")
            print("[NOTIFICATION_SERVICE] Calling consume_messages with queue='notification.payment.completed', routing_key='payment.completed'")
            consume_messages("notification.payment.completed", handle_payment_completed, routing_key="payment.completed")
        except Exception as e:
            print(f"[NOTIFICATION_SERVICE] Error in payment completed consumer: {e}")
            import traceback
            traceback.print_exc()
    
    # Payment failed consumer (ayrı thread'de)
    def start_payment_failed_consumer():
        try:
            print("[NOTIFICATION_SERVICE] Starting payment.failed consumer thread...")
            consume_messages("notification.payment.failed", handle_payment_failed, routing_key="payment.failed")
        except Exception as e:
            print(f"[NOTIFICATION_SERVICE] Error in payment failed consumer: {e}")
            import traceback
            traceback.print_exc()
    
    # Her consumer'ı ayrı thread'de başlat
    print("[NOTIFICATION_SERVICE] Creating threads for consumers...")
    thread1 = threading.Thread(target=start_payment_completed_consumer, daemon=True)
    thread1.start()
    print(f"[NOTIFICATION_SERVICE] Payment completed consumer thread started: {thread1.is_alive()}, name={thread1.name}")
    
    thread2 = threading.Thread(target=start_payment_failed_consumer, daemon=True)
    thread2.start()
    print(f"[NOTIFICATION_SERVICE] Payment failed consumer thread started: {thread2.is_alive()}, name={thread2.name}")
    
    print("[NOTIFICATION_SERVICE] Notification consumers started in background threads")

