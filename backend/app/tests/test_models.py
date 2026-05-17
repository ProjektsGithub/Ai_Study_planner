"""
Tests for database models
"""
import pytest
from datetime import datetime, date, time
from app.models import (
    User,
    StudentProfile,
    Subject,
    Availability,
    Constraint,
    StudyPlan,
    StudySession,
    GenerationLog,
    Notification,
)


def test_user_model():
    """Test User model instantiation"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User",
        created_at=datetime.utcnow(),
        is_active=True,
        failed_login_attempts=0,
    )
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active is True
    assert user.failed_login_attempts == 0


def test_student_profile_model():
    """Test StudentProfile model instantiation"""
    profile = StudentProfile(
        user_id=1,
        cursus="Computer Science",
        academic_level="Bachelor Year 3",
        weekly_study_goal=25.0,
        preferences={"theme": "dark"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert profile.cursus == "Computer Science"
    assert profile.weekly_study_goal == 25.0
    assert profile.preferences["theme"] == "dark"


def test_subject_model():
    """Test Subject model instantiation"""
    subject = Subject(
        user_id=1,
        name="Algorithms",
        priority=5,
        difficulty=4,
        target_weekly_hours=6.0,
        exam_date=date(2026, 6, 1),
        created_at=datetime.utcnow(),
    )
    assert subject.name == "Algorithms"
    assert subject.priority == 5
    assert subject.difficulty == 4
    assert subject.target_weekly_hours == 6.0


def test_availability_model():
    """Test Availability model instantiation"""
    availability = Availability(
        user_id=1,
        day_of_week="Monday",
        start_time=time(18, 0),
        end_time=time(22, 0),
        created_at=datetime.utcnow(),
    )
    assert availability.day_of_week == "Monday"
    assert availability.start_time == time(18, 0)
    assert availability.end_time == time(22, 0)


def test_constraint_model():
    """Test Constraint model instantiation"""
    constraint = Constraint(
        user_id=1,
        constraint_type="max_daily_hours",
        parameters={"max_hours": 4.0},
        active=True,
        created_at=datetime.utcnow(),
    )
    assert constraint.constraint_type == "max_daily_hours"
    assert constraint.parameters["max_hours"] == 4.0
    assert constraint.active is True


def test_study_plan_model():
    """Test StudyPlan model instantiation"""
    plan = StudyPlan(
        plan_id="550e8400-e29b-41d4-a716-446655440000",
        user_id=1,
        week_start=date(2026, 5, 11),
        status="generated",
        summary="Test plan",
        edited=False,
        created_at=datetime.utcnow(),
    )
    assert plan.plan_id == "550e8400-e29b-41d4-a716-446655440000"
    assert plan.status == "generated"
    assert plan.edited is False


def test_study_session_model():
    """Test StudySession model instantiation"""
    session = StudySession(
        study_plan_id=1,
        subject_id=1,
        day="Monday",
        start_time=time(18, 0),
        end_time=time(20, 0),
        task_type="revision",
        notes="Focus on algorithms",
    )
    assert session.day == "Monday"
    assert session.task_type == "revision"
    assert session.notes == "Focus on algorithms"


def test_generation_log_model():
    """Test GenerationLog model instantiation"""
    log = GenerationLog(
        user_id=1,
        request_hash="abc123",
        duration_seconds=2.5,
        token_count=150,
        success=True,
        created_at=datetime.utcnow(),
    )
    assert log.request_hash == "abc123"
    assert log.duration_seconds == 2.5
    assert log.success is True


def test_notification_model():
    """Test Notification model instantiation"""
    notification = Notification(
        user_id=1,
        notification_type="plan_generated",
        message="Your study plan has been generated",
        read=False,
        created_at=datetime.utcnow(),
    )
    assert notification.notification_type == "plan_generated"
    assert notification.read is False
    assert "generated" in notification.message
