"""
Notifications API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user notifications
    
    Args:
        unread_only: Filter for unread notifications
        limit: Maximum number of notifications
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of notifications with unread count
    """
    service = NotificationService(db)
    
    notifications = service.get_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    
    unread_count = service.get_unread_count(current_user.id)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "total": len(notifications)
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of unread notifications
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Unread notification count
    """
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)
    
    return {"unread_count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated notification
        
    Raises:
        404: Notification not found
    """
    service = NotificationService(db)
    
    notification = service.mark_as_read(notification_id, current_user.id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    
    return notification


@router.put("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all user notifications as read
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Number of notifications updated
    """
    service = NotificationService(db)
    count = service.mark_all_as_read(current_user.id)
    
    return {
        "message": f"{count} notifications marked as read",
        "count": count
    }
