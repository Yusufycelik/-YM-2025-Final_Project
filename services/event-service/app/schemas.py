from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import EventStatus, EventCategory


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: EventCategory
    venue: str
    city: str
    address: Optional[str] = None
    start_date: datetime
    end_date: datetime
    base_price: float
    total_capacity: int
    image_url: Optional[str] = None


class EventCreate(EventBase):
    organizer_id: int


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    base_price: Optional[float] = None
    total_capacity: Optional[int] = None
    status: Optional[EventStatus] = None
    image_url: Optional[str] = None


class EventResponse(EventBase):
    id: int
    available_tickets: int
    status: EventStatus
    organizer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

