"""
Tests for PDF Export Service
"""
import uuid
import pytest
from datetime import datetime, time as dt_time
from io import BytesIO

from app.services.export_service import ExportService, SUBJECT_PALETTE
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession


@pytest.mark.asyncio
async def test_generate_pdf_success(db_session):
    """Test successful PDF generation"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()

    profile = StudentProfile(
        user_id=user.id,
        cursus="Computer Science",
        academic_level="Bachelor",
        weekly_study_goal=20.0,
    )
    db_session.add(profile)

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

    export_service = ExportService(db_session)
    pdf_buffer = await export_service.generate_pdf(plan.id, user)

    assert isinstance(pdf_buffer, BytesIO)
    assert pdf_buffer.tell() == 0

    pdf_buffer.seek(0, 2)
    size = pdf_buffer.tell()
    assert size > 0
    assert size < ExportService.MAX_FILE_SIZE


@pytest.mark.asyncio
async def test_generate_pdf_empty_plan(db_session):
    """Test PDF generation for empty plan"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    export_service = ExportService(db_session)
    pdf_buffer = await export_service.generate_pdf(plan.id, user)

    assert isinstance(pdf_buffer, BytesIO)
    pdf_buffer.seek(0, 2)
    size = pdf_buffer.tell()
    assert size > 0


@pytest.mark.asyncio
async def test_generate_pdf_plan_not_found(db_session):
    """Test PDF generation with non-existent plan"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()

    export_service = ExportService(db_session)

    with pytest.raises(ValueError, match="999"):
        await export_service.generate_pdf(999, user)


@pytest.mark.asyncio
async def test_generate_pdf_multiple_sessions(db_session):
    """Test PDF generation with multiple sessions"""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()

    subjects = []
    for i in range(3):
        subject = Subject(
            user_id=user.id,
            name=f"Subject {i + 1}",
            priority=5,
            difficulty=3,
            target_weekly_hours=3.0,
        )
        db_session.add(subject)
        subjects.append(subject)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    days = ["Monday", "Tuesday", "Wednesday"]
    for day in days:
        for j, subject in enumerate(subjects):
            session = StudySession(
                study_plan_id=plan.id,
                subject_id=subject.id,
                day=day,
                start_time=dt_time(9 + j * 2, 0),
                end_time=dt_time(10 + j * 2, 30),
                task_type="lecture_review",
            )
            db_session.add(session)
    db_session.commit()

    export_service = ExportService(db_session)
    pdf_buffer = await export_service.generate_pdf(plan.id, user)

    assert isinstance(pdf_buffer, BytesIO)
    pdf_buffer.seek(0, 2)
    size = pdf_buffer.tell()
    assert size > 0
    assert size < ExportService.MAX_FILE_SIZE


@pytest.mark.asyncio
async def test_pdf_timeout(db_session, monkeypatch):
    """Test PDF generation timeout"""
    import asyncio

    user = User(
        email="test@example.com",
        name="Test User",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(10)
        return BytesIO()

    export_service = ExportService(db_session)
    monkeypatch.setattr(export_service, "TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(export_service, "_generate_pdf_internal", slow_generate)

    with pytest.raises(TimeoutError):
        await export_service.generate_pdf(plan.id, user)


def test_export_service_constants():
    """Test ExportService constants"""
    assert ExportService.MAX_FILE_SIZE == 10 * 1024 * 1024
    assert ExportService.TIMEOUT_SECONDS == 15
    assert len(ExportService.DAYS_OF_WEEK) == 7
    assert len(SUBJECT_PALETTE) == 10
