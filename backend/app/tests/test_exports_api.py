"""
Integration tests for Exports API
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, time as dt_time

from app.main import app
from app.core.dependencies import get_db
from app.models.user import User
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession


client = TestClient(app)


@pytest.fixture(autouse=True)
def override_db_dependency(db_session):
    """Ensure FastAPI TestClient uses the in-memory test db_session."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db, None)


def test_export_pdf_success(db_session, auth_headers):
    """Test successful PDF export"""
    user = db_session.query(User).filter(User.email == "test@example.com").first()

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

    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert f"study_plan_{plan.id}.pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_pdf_empty_plan(db_session, auth_headers):
    """Test PDF export for empty plan"""
    user = db_session.query(User).filter(User.email == "test@example.com").first()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_export_pdf_plan_not_found(auth_headers):
    """Test PDF export with non-existent plan"""
    response = client.post(
        "/api/v1/exports/plans/999/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "999" in response.json()["detail"].lower()


def test_export_pdf_unauthorized():
    """Test PDF export without authentication"""
    response = client.post("/api/v1/exports/plans/1/pdf")

    assert response.status_code == 401


def test_export_pdf_other_user_plan(db_session, auth_headers):
    """Test PDF export for another user's plan"""
    other_user = User(
        email="other@example.com",
        name="Other User",
        password_hash="hashed",
    )
    db_session.add(other_user)
    db_session.commit()

    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=other_user.id,
        week_start=datetime.now().date(),
        status="generated",
    )
    db_session.add(plan)
    db_session.commit()

    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 404
