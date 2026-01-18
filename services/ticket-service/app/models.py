from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, ForeignKey
from sqlalchemy.sql import func
import enum
from app.database import Base


class TicketStatus(str, enum.Enum):
    RESERVED = "reserved"  # Rezerve edildi, ödeme bekleniyor
    CONFIRMED = "confirmed"  # Ödeme yapıldı, onaylandı
    CANCELLED = "cancelled"  # İptal edildi
    USED = "used"  # Kullanıldı


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    event_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    
    # Ticket details
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Status
    status = Column(Enum(TicketStatus), default=TicketStatus.RESERVED)
    
    # Payment
    payment_id = Column(Integer, nullable=True)  # Payment ID from payment-service
    
    # Metadata
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

