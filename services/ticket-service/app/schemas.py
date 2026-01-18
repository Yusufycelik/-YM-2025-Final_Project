from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import TicketStatus


class TicketBase(BaseModel):
    event_id: int
    quantity: int
    unit_price: float
    total_price: float


class TicketCreate(BaseModel):
    event_id: int
    user_id: int
    quantity: int


class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    user_id: int
    status: TicketStatus
    payment_id: Optional[int] = None
    reserved_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    payment_id: Optional[int] = None


class AdminTicketCreate(BaseModel):
    """Admin için kullanıcıya bilet atama"""
    event_id: int
    user_id: int
    quantity: int
