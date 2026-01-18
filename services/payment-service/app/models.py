from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, Text
from sqlalchemy.sql import func
import enum
from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String, unique=True, index=True, nullable=False)
    ticket_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="TRY")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Transaction details
    transaction_id = Column(String, nullable=True)  # External payment gateway transaction ID
    failure_reason = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

