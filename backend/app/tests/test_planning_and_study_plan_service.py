"""
Tests for PlanningEngine and StudyPlanService end-to-end orchestration
(including fallback plan persistence when Colab/Ollama is offline).
"""
from datetime import date, time, timedelta
from unittest.mock import patch
import pytest
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.services.planning_engine import PlanningEngine, TimeSlot
from app.services.study_plan_service import StudyPlanService


def _seed_student_data(db_session: Session, user: User) -> None:
    profile = StudentProfile(
        user_id=user.id,
        cursus="Computer Science",
        academic_level="Bachelor 3",
        weekly_study_goal=10.0,
        preferred_study_time="morning",
        preferred_session_duration=90,
        study_pace="moderate",
    )
    db_session.add(profile)

    s1 = Subject(
        user_id=user.id,
        name="Algorithmique",
        priority=5,
        difficulty=5,
        target_weekly_hours=5.0,
        exam_date=date.today() + timedelta(days=10),
        ects_credits=6.0,
        coefficient=3.0,
        is_mandatory=True,
        validation_status="failed",
    )
    s2 = Subject(
        user_id=user.id,
        name="Bases de données",
        priority=3,
        difficulty=3,
        target_weekly_hours=3.0,
        ects_credits=4.0,
        coefficient=1.5,
        is_mandatory=True,
        validation_status="in_progress",
    )
    db_session.add_all([s1, s2])

    a1 = Availability(
        user_id=user.id,
        day_of_week="Monday",
        start_time=time(9, 0),
        end_time=time(12, 0),
        energy_level="high",
    )
    a2 = Availability(
        user_id=user.id,
        day_of_week="Thursday",
        start_time=time(14, 0),
        end_time=time(17, 0),
        energy_level="medium",
    )
    db_session.add_all([a1, a2])

    c1 = Constraint(
        user_id=user.id,
        constraint_type="max_daily_hours",
        parameters={"max_hours": 4.0},
        active=True,
    )
    db_session.add(c1)
    db_session.commit()


def test_timeslot_overlap_and_duration():
    slot_a = TimeSlot("Monday", time(9, 0), time(10, 30))
    slot_b = TimeSlot("Monday", time(10, 0), time(11, 30))
    slot_c = TimeSlot("Tuesday", time(9, 0), time(10, 30))

    assert slot_a.duration_minutes == 90
    assert slot_a.overlaps_with(slot_b) is True
    assert slot_a.overlaps_with(slot_c) is False


def test_planning_engine_prioritizes_failed_retake_subject(db_session: Session, test_user: User):
    _seed_student_data(db_session, test_user)

    engine = PlanningEngine(test_user.id, db_session)
    planning_data = engine.generate_planning_data(db=db_session)

    assert len(planning_data["valid_slots"]) >= 2
    priorities = planning_data["subject_priorities"]
    assert len(priorities) == 2
    # Failed mandatory subject with upcoming exam must rank first
    assert priorities[0]["subject_name"] == "Algorithmique"
    assert priorities[0]["priority_score"] > priorities[1]["priority_score"]


@pytest.mark.asyncio
async def test_study_plan_service_generates_and_saves_with_fallback(db_session: Session, test_user: User):
    _seed_student_data(db_session, test_user)

    service = StudyPlanService(db_session)
    monday = date.today() - timedelta(days=date.today().weekday())

    # Simulate Colab/Ollama being unreachable -> StudyPlanService must still succeed via fallback
    with patch.object(service.ai_service, "_call_colab_api", side_effect=Exception("Colab offline")), \
         patch.object(service.ai_service, "_call_ollama_api", side_effect=Exception("Ollama offline")):
        success, result = await service.generate_plan(
            user_id=test_user.id,
            week_start=monday,
            force_regenerate=True,
            language="fr",
        )

    assert success is True
    current = service.get_current_plan(test_user.id)
    assert current is not None
    assert len(current.get("sessions", [])) >= 2

