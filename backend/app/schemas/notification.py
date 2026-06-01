"""
Notification schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class NotificationBase(BaseModel):
    """Base notification schema"""
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")


class NotificationResponse(NotificationBase):
    """Notification response schema"""
    id: int
    user_id: int
    read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications with metadata"""
    notifications: List[NotificationResponse]
    unread_count: int
    total: int


class UnreadCountResponse(BaseModel):
    """Unread notification count"""
    unread_count: int
