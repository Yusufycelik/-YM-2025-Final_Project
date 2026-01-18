from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import PaymentStatus, PaymentMethod


class PaymentBase(BaseModel):
    ticket_id: int
    amount: float
    payment_method: PaymentMethod
    currency: str = "TRY"


class PaymentCreate(BaseModel):
    ticket_id: int
    user_id: int
    payment_method: PaymentMethod
    currency: str = "TRY"
    # Simülasyon için kart bilgileri (gerçek uygulamada güvenli şekilde işlenmeli)
    card_number: Optional[str] = None  # Son 4 hanesi kontrol için
    card_holder_name: Optional[str] = None
    expiry_date: Optional[str] = None  # MM/YY formatında
    cvv: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int
    payment_number: str
    user_id: int
    status: PaymentStatus
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None

