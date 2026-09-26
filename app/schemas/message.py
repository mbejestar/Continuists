from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class MessageCreate(BaseModel):
    recipient_continuum_id: str
    mission_id: Optional[UUID] = None
    content: str = Field(..., min_length=1, max_length=5000)

class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    recipient_id: UUID
    mission_id: Optional[UUID] = None
    content: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
