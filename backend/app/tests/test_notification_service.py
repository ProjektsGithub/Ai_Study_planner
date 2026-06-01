"""
Tests for Notification Service
"""
import pytest
from datetime import datetime, timedelta, time as dt_time

from app.services.notification_service import NotificationService
from app.models.user import User
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.notification import Notification


def test_create_plan_generated_notification(db_session):
    """Test creating plan generation notification"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create plan
    plan = StudyPlan(
        user_id=user.id,
        week_start_date=datetime.now().date(),
        total_hours=10.0,
        status="generated"
    )
    db_session.add(plan)
    db_session.commit()
    
    # Create notification
    service = NotificationService(db_session)
    notification = service.create_plan_generated_notification(user.id, plan)
    
    # Assertions
    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.notification_type == NotificationService.TYPE_PLAN_GENERATED
    assert "10.0 heures" in notification.message
    assert notification.read == False


def test_create_session_reminder(db_session):
    """Test creating session reminder"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create subject
    subject = Subject(
        user_id=user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=5.0
    )
    db_session.add(subject)
    db_session.commit()
    
    # Create plan
    plan = StudyPlan(
        user_id=user.id,
        week_start_date=datetime.now().date(),
        total_hours=5.0,
        status="generated"
    )
    db_session.add(plan)
    db_session.commit()
    
    # Create session
    session = StudySession(
        study_plan_id=plan.id,
        subject_id=subject.id,
        day="Monday",
        start_time=dt_time(9, 0),
        end_time=dt_time(10, 30),
        task_type="lecture"
    )
    db_session.add(session)
    db_session.commit()
    
    # Create reminder
    service = NotificationService(db_session)
    notification = service.create_session_reminder(user.id, session)
    
    # Assertions
    assert notification is not None
    assert notification.user_id == user.id
    assert notification.notification_type == NotificationService.TYPE_SESSION_REMINDER
    assert "Mathematics" in notification.message
    assert "30 minutes" in notification.message
    assert notification.read == False


def test_duplicate_reminder_prevention(db_session):
    """Test that duplicate reminders are prevented"""
    # Setup
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    subject = Subject(
        user_id=user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=5.0
    )
    db_session.add(subject)
    db_session.commit()
    
    plan = StudyPlan(
        user_id=user.id,
        week_start_date=datetime.now().date(),
        total_hours=5.0,
        status="generated"
    )
    db_session.add(plan)
    db_session.commit()
    
    session = StudySession(
        study_plan_id=plan.id,
        subject_id=subject.id,
        day="Monday",
        start_time=dt_time(9, 0),
        end_time=dt_time(10, 30),
        task_type="lecture"
    )
    db_session.add(session)
    db_session.commit()
    
    # Create first reminder
    service = NotificationService(db_session)
    notification1 = service.create_session_reminder(user.id, session)
    assert notification1 is not None
    
    # Try to create duplicate
    notification2 = service.create_session_reminder(user.id, session)
    assert notification2 is None  # Should be prevented


def test_get_notifications(db_session):
    """Test getting user notifications"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create notifications
    for i in range(5):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test notification {i}",
            read=(i % 2 == 0)  # Alternate read/unread
        )
        db_session.add(notif)
    db_session.commit()
    
    # Get all notifications
    service = NotificationService(db_session)
    all_notifs = service.get_notifications(user.id, unread_only=False)
    assert len(all_notifs) == 5
    
    # Get unread only
    unread_notifs = service.get_notifications(user.id, unread_only=True)
    assert len(unread_notifs) == 2


def test_mark_as_read(db_session):
    """Test marking notification as read"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create notification
    notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Test",
        read=False
    )
    db_session.add(notif)
    db_session.commit()
    
    # Mark as read
    service = NotificationService(db_session)
    updated = service.mark_as_read(notif.id, user.id)
    
    assert updated is not None
    assert updated.read == True


def test_mark_all_as_read(db_session):
    """Test marking all notifications as read"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create unread notifications
    for i in range(3):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test {i}",
            read=False
        )
        db_session.add(notif)
    db_session.commit()
    
    # Mark all as read
    service = NotificationService(db_session)
    count = service.mark_all_as_read(user.id)
    
    assert count == 3
    
    # Verify
    unread = service.get_notifications(user.id, unread_only=True)
    assert len(unread) == 0


def test_delete_old_notifications(db_session):
    """Test deleting old notifications"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create old notification
    old_notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Old notification",
        read=True
    )
    db_session.add(old_notif)
    db_session.flush()
    
    # Manually set old date
    old_date = datetime.now() - timedelta(days=35)
    db_session.query(Notification).filter(
        Notification.id == old_notif.id
    ).update({"created_at": old_date})
    db_session.commit()
    
    # Create recent notification
    recent_notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Recent notification",
        read=False
    )
    db_session.add(recent_notif)
    db_session.commit()
    
    # Delete old notifications
    service = NotificationService(db_session)
    count = service.delete_old_notifications()
    
    assert count == 1
    
    # Verify only recent remains
    all_notifs = service.get_notifications(user.id, unread_only=False)
    assert len(all_notifs) == 1
    assert all_notifs[0].message == "Recent notification"


def test_get_unread_count(db_session):
    """Test getting unread notification count"""
    # Create user
    user = User(email="test@example.com", hashed_password="test")
    db_session.add(user)
    db_session.commit()
    
    # Create notifications
    for i in range(5):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test {i}",
            read=(i < 2)  # First 2 are read
        )
        db_session.add(notif)
    db_session.commit()
    
    # Get unread count
    service = NotificationService(db_session)
    count = service.get_unread_count(user.id)
    
    assert count == 3
