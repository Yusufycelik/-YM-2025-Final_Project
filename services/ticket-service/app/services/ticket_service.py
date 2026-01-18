from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
import uuid
from datetime import datetime
from app.models import Ticket, TicketStatus
from app.schemas import TicketCreate, TicketUpdate
from app.utils.rabbitmq import publish_message
import httpx
from app.config import settings


def generate_ticket_number() -> str:
    """Benzersiz bilet numarası oluştur"""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


def get_ticket(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_ticket_by_number(db: Session, ticket_number: str):
    return db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()


def get_user_tickets(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Ticket).filter(Ticket.user_id == user_id).offset(skip).limit(limit).all()


def get_event_tickets(db: Session, event_id: int):
    return db.query(Ticket).filter(Ticket.event_id == event_id).all()


async def create_ticket(db: Session, ticket: TicketCreate):
    """Bilet rezervasyonu oluştur"""
    # Event bilgilerini event-service'den al
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.EVENT_SERVICE_URL}/api/v1/events/{ticket.event_id}")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found"
                )
            event_data = response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event service unavailable"
        )
    
    # Stok kontrolü
    if event_data["available_tickets"] < ticket.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough tickets available"
        )
    
    # Bilet limiti kaldırıldı - kullanıcılar istediği kadar bilet alabilir
    
    # Fiyat hesapla
    unit_price = event_data["base_price"]
    total_price = unit_price * ticket.quantity
    
    # Bilet oluştur
    ticket_number = generate_ticket_number()
    db_ticket = Ticket(
        ticket_number=ticket_number,
        event_id=ticket.event_id,
        user_id=ticket.user_id,
        quantity=ticket.quantity,
        unit_price=unit_price,
        total_price=total_price,
        status=TicketStatus.RESERVED
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Event service'e stok güncellemesi için mesaj gönder
    publish_message(
        exchange="events",
        routing_key="ticket.reserved",
        message={
            "event_id": ticket.event_id,
            "quantity": ticket.quantity,
            "ticket_id": db_ticket.id
        }
    )
    
    # NOT: Notification service'e bildirim göndermiyoruz çünkü:
    # - Ödeme henüz yapılmadı, sadece rezervasyon yapıldı
    # - Ödeme başarılı olduğunda Payment Service bildirim gönderecek
    # - Bu sayede kullanıcıya sadece ödeme başarılı olduğunda bildirim gider
    
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    update_data = ticket_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)
    
    if ticket_update.status == TicketStatus.CONFIRMED:
        db_ticket.confirmed_at = datetime.utcnow()
    elif ticket_update.status == TicketStatus.CANCELLED:
        db_ticket.cancelled_at = datetime.utcnow()
        # Stok geri ver
        publish_message(
            exchange="events",
            routing_key="ticket.cancelled",
            message={
                "event_id": db_ticket.event_id,
                "quantity": db_ticket.quantity
            }
        )
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def cancel_ticket(db: Session, ticket_id: int):
    """Bilet iptali"""
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if db_ticket.status == TicketStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket already cancelled"
        )
    
    if db_ticket.status == TicketStatus.USED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel used ticket"
        )
    
    db_ticket.status = TicketStatus.CANCELLED
    db_ticket.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    
    # Event service'e stok geri verme mesajı
    publish_message(
        exchange="events",
        routing_key="ticket.cancelled",
        message={
            "event_id": db_ticket.event_id,
            "quantity": db_ticket.quantity
        }
    )
    
    return db_ticket

