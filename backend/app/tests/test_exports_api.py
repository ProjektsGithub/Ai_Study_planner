"""
Integration tests for Exports API
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession


client = TestClient(app)


def test_export_pdf_success(db_session, auth_headers):
    """Test successful PDF export"""
    # Get user from auth_headers
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    
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
    
    # Create study plan
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
        start_time="09:00",
        end_time="10:30",
        task_type="lecture"
    )
    db_session.add(session)
    db_session.commit()
    
    # Export PDF
    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert f"study_plan_{plan.id}.pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_pdf_empty_plan(db_session, auth_headers):
    """Test PDF export for empty plan"""
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    
    # Create empty plan
    plan = StudyPlan(
        user_id=user.id,
        week_start_date=datetime.now().date(),
        total_hours=0.0,
        status="generated"
    )
    db_session.add(plan)
    db_session.commit()
    
    # Export PDF
    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_export_pdf_plan_not_found(auth_headers):
    """Test PDF export with non-existent plan"""
    response = client.post(
        "/api/v1/exports/plans/999/pdf",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_export_pdf_unauthorized():
    """Test PDF export without authentication"""
    response = client.post("/api/v1/exports/plans/1/pdf")
    
    assert response.status_code == 401


def test_export_pdf_other_user_plan(db_session, auth_headers):
    """Test PDF export for another user's plan"""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Create plan for other user
    plan = StudyPlan(
        user_id=other_user.id,
        week_start_date=datetime.now().date(),
        total_hours=0.0,
        status="generated"
    )
    db_session.add(plan)
    db_session.commit()
    
    # Try to export
    response = client.post(
        f"/api/v1/exports/plans/{plan.id}/pdf",
        headers=auth_headers
    )
    
    # Should not find plan (filtered by user_id)
    assert response.status_code == 404
