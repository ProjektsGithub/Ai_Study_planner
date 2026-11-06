"""
Tests for Notification Service
"""
import uuid
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
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    subject = Subject(
        user_id=user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=5.0,
    )
    db_session.add(subject)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    session = StudySession(
        study_plan_id=plan.id,
        subject_id=subject.id,
        day="Monday",
        start_time=dt_time(9, 0),
        end_time=dt_time(11, 0),
        task_type="lecture_review",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(plan)

    service = NotificationService(db_session)
    notification = service.create_plan_generated_notification(user.id, plan)

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.notification_type == NotificationService.TYPE_PLAN_GENERATED
    assert "2.0 heures" in notification.message
    assert notification.read is False


def test_create_session_reminder(db_session):
    """Test creating session reminder"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    subject = Subject(
        user_id=user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=5.0,
    )
    db_session.add(subject)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    session = StudySession(
        study_plan_id=plan.id,
        subject_id=subject.id,
        day="Monday",
        start_time=dt_time(9, 0),
        end_time=dt_time(10, 30),
        task_type="lecture_review",
    )
    db_session.add(session)
    db_session.commit()

    service = NotificationService(db_session)
    notification = service.create_session_reminder(user.id, session)

    assert notification is not None
    assert notification.user_id == user.id
    assert notification.notification_type == NotificationService.TYPE_SESSION_REMINDER
    assert "Mathematics" in notification.message
    assert "30 minutes" in notification.message
    assert notification.read is False


def test_duplicate_reminder_prevention(db_session):
    """Test that duplicate reminders are prevented"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    subject = Subject(
        user_id=user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=5.0,
    )
    db_session.add(subject)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    session = StudySession(
        study_plan_id=plan.id,
        subject_id=subject.id,
        day="Monday",
        start_time=dt_time(9, 0),
        end_time=dt_time(10, 30),
        task_type="lecture_review",
    )
    db_session.add(session)
    db_session.commit()

    service = NotificationService(db_session)
    notification1 = service.create_session_reminder(user.id, session)
    assert notification1 is not None

    notification2 = service.create_session_reminder(user.id, session)
    assert notification2 is None


def test_get_notifications(db_session):
    """Test getting user notifications"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    for i in range(5):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test notification {i}",
            read=(i % 2 == 0),
        )
        db_session.add(notif)
    db_session.commit()

    service = NotificationService(db_session)
    all_notifs = service.get_notifications(user.id, unread_only=False)
    assert len(all_notifs) == 5

    unread_notifs = service.get_notifications(user.id, unread_only=True)
    assert len(unread_notifs) == 2


def test_mark_as_read(db_session):
    """Test marking notification as read"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Test",
        read=False,
    )
    db_session.add(notif)
    db_session.commit()

    service = NotificationService(db_session)
    updated = service.mark_as_read(notif.id, user.id)

    assert updated is not None
    assert updated.read is True


def test_mark_all_as_read(db_session):
    """Test marking all notifications as read"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    for i in range(3):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test {i}",
            read=False,
        )
        db_session.add(notif)
    db_session.commit()

    service = NotificationService(db_session)
    count = service.mark_all_as_read(user.id)

    assert count == 3

    unread = service.get_notifications(user.id, unread_only=True)
    assert len(unread) == 0


def test_delete_old_notifications(db_session):
    """Test deleting old notifications"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    old_notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Old notification",
        read=True,
    )
    db_session.add(old_notif)
    db_session.flush()

    old_date = datetime.now() - timedelta(days=35)
    db_session.query(Notification).filter(
        Notification.id == old_notif.id
    ).update({"created_at": old_date})
    db_session.commit()

    recent_notif = Notification(
        user_id=user.id,
        notification_type="system_alert",
        message="Recent notification",
        read=False,
    )
    db_session.add(recent_notif)
    db_session.commit()

    service = NotificationService(db_session)
    count = service.delete_old_notifications()

    assert count == 1

    all_notifs = service.get_notifications(user.id, unread_only=False)
    assert len(all_notifs) == 1
    assert all_notifs[0].message == "Recent notification"


def test_get_unread_count(db_session):
    """Test getting unread notification count"""
    user = User(email="test@example.com", name="Test User", password_hash="test")
    db_session.add(user)
    db_session.commit()

    for i in range(5):
        notif = Notification(
            user_id=user.id,
            notification_type="system_alert",
            message=f"Test {i}",
            read=(i < 2),
        )
        db_session.add(notif)
    db_session.commit()

    service = NotificationService(db_session)
    count = service.get_unread_count(user.id)

    assert count == 3
