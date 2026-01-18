from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventCategory(str, enum.Enum):
    CONCERT = "concert"
    THEATER = "theater"
    SPORTS = "sports"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    FESTIVAL = "festival"
    OTHER = "other"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(EventCategory), default=EventCategory.OTHER)
    venue = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    
    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Pricing
    base_price = Column(Float, nullable=False, default=0.0)
    
    # Capacity
    total_capacity = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    
    # Status
    status = Column(Enum(EventStatus), default=EventStatus.DRAFT)
    
    # Organizer
    organizer_id = Column(Integer, nullable=False)  # User ID from user-service
    
    # Metadata
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

