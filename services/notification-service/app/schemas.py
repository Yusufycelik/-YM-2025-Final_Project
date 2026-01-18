from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models import NotificationType, NotificationStatus


class NotificationBase(BaseModel):
    user_id: int
    notification_type: NotificationType
    subject: Optional[str] = None
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: int
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

