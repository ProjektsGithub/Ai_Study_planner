"""
Unit tests for AIService prompt engineering, JSON extraction/sanitization,
and deterministic fallback plan generation (including SSE streaming fallback).
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

import app.models  # noqa: F401 — ensure all mappers are registered
from app.services.ai_service import AIService
from app.models.user import User


def _sample_planning_data(num_subjects: int = 3, num_slots_per_day: int = 2) -> dict:
    days = ["Monday", "Wednesday", "Friday"]
    valid_slots = []
    for day in days:
        for i in range(num_slots_per_day):
            hour = 9 + i * 2
            valid_slots.append({
                "day": day,
                "start_time": f"{hour:02d}:00:00",
                "end_time": f"{hour + 1:02d}:30:00",
                "duration_minutes": 90,
                "energy_level": "high" if i == 0 else "medium",
            })

    subject_priorities = []
    for idx in range(num_subjects):
        subject_priorities.append({
            "subject_name": f"Subject_{idx + 1}",
            "priority_score": float(90 - idx * 5),
            "target_weekly_hours": 4.0,
            "ects_credits": 6.0,
            "coefficient": 2.0,
            "is_mandatory": idx < 2,
            "validation_status": "failed" if idx == 0 else "in_progress",
            "exam_date": "2026-12-01" if idx == 0 else None,
            "exam_type": "final" if idx == 0 else None,
            "current_progress": 30.0,
            "weak_topics": ["Topic A", "Topic B"] if idx == 0 else [],
        })

    return {
        "valid_slots": valid_slots,
        "subject_priorities": subject_priorities,
        "constraints": {
            "max_daily_hours": 5.0,
            "required_breaks": [{"duration_minutes": 15, "after_minutes": 90}],
            "fixed_slots": [],
        },
        "academic_schedule": [
            {
                "day_of_week": "Tuesday",
                "start_time": "08:30:00",
                "end_time": "10:30:00",
                "course_name": "Subject_1",
                "course_code": "CS101",
                "session_type": "CM",
                "room_location": "Amphi A",
            }
        ],
        "academic_context": {
            "academic_progress": {
                "ects_obtained": 60,
                "ects_required": 180,
                "progression_percentage": 33.3,
            },
            "failed_courses": [
                {
                    "course_name": "Subject_1",
                    "attempt_count": 2,
                    "days_since_first_failure": 120,
                    "is_prerequisite_blocker": True,
                }
            ],
            "course_priorities": [
                {
                    "course_name": "Subject_1",
                    "priority_score": 90,
                    "risk_level": "high",
                    "recommended_weekly_hours": 5,
                    "success_probability": 45,
                }
            ],
            "upcoming_exams": [
                {
                    "course_name": "Subject_1",
                    "exam_date": "2026-12-01",
                    "days_until": 5,
                }
            ],
            "student_profile": {
                "cursus_name": "Computer Science",
                "current_semester": 5,
            },
        },
    }


class TestConstructPrompt:
    """Tests for AIService._construct_prompt token budget, constraints, and localization."""

    def test_construct_prompt_french_default_and_allowed_days(self, db_session: Session):
        ai = AIService(db_session)
        data = _sample_planning_data()
        prompt = ai._construct_prompt(
            planning_data=data,
            weekly_study_goal=18.0,
            user_preferences={"preferred_study_times": ["morning"], "session_length": 90, "break_duration": 15},
            profile_context={"semester_start_date": "2026-09-01", "semester_end_date": "2027-01-31"},
            language="fr",
        )

        assert "FRANÇAIS" in prompt
        assert "ALLOWED: Friday, Monday, Wednesday" in prompt
        assert "FORBIDDEN" in prompt
        assert "Tuesday" in prompt  # Forbidden day listed
        assert "Subject_1" in prompt
        assert "[PREREQUISITE BLOCKER]" in prompt
        assert len(prompt) < 6500  # Compactness guard for Colab 2048/8192 context

    @pytest.mark.parametrize(
        "lang,expected_marker",
        [
            ("en", "MANDATORY OUTPUT LANGUAGE: ENGLISH"),
            ("de", "PFLICHT-AUSGABESPRACHE: DEUTSCH"),
            ("fr", "LANGUE DE SORTIE OBLIGATOIRE : FRANÇAIS"),
        ],
    )
    def test_construct_prompt_multilingual_markers(self, db_session: Session, lang: str, expected_marker: str):
        ai = AIService(db_session)
        prompt = ai._construct_prompt(
            planning_data=_sample_planning_data(),
            weekly_study_goal=15.0,
            user_preferences={},
            language=lang,
        )
        assert expected_marker in prompt

    def test_construct_prompt_caps_subjects_and_slots(self, db_session: Session):
        ai = AIService(db_session)
        # 15 subjects and 8 slots per day -> must be capped to 8 subjects and 4 slots/day
        data = _sample_planning_data(num_subjects=15, num_slots_per_day=8)
        prompt = ai._construct_prompt(
            planning_data=data,
            weekly_study_goal=20.0,
            user_preferences={},
            language="fr",
        )
        # Top 8 subjects present (Subject_1..Subject_8), Subject_15 excluded
        assert "Subject_1" in prompt
        assert "Subject_8" in prompt
        assert "Subject_15" not in prompt
        assert len(prompt) < 6500


class TestExtractJsonFromResponse:
    """Tests for AIService._extract_json_from_response resilience and sanitization."""

    def test_extract_clean_json(self, db_session: Session):
        ai = AIService(db_session)
        raw = json.dumps({
            "sessions": [
                {
                    "day": "Monday",
                    "start_time": "09:00:00",
                    "end_time": "10:30:00",
                    "subject_name": "Mathématiques",
                    "task_type": "lecture_review",
                    "notes": "Théorèmes de convergence des suites réelles",
                }
            ],
            "total_hours": 1.5,
            "reasoning": "Progression pédagogique",
        })
        res = ai._extract_json_from_response(raw)
        assert res is not None
        assert len(res["sessions"]) == 1
        assert res["total_hours"] == 1.5

    def test_extract_json_from_markdown_and_double_braces(self, db_session: Session):
        ai = AIService(db_session)
        raw = """Here is your schedule:
```json
{{"sessions":[{{"day":"Monday","start_time":"09:00:00","end_time":"11:00:00","subject_name":"Algorithmique","task_type":"exercise_practice","notes":"Graphes et parcours BFS/DFS"}}],"total_hours":0,"reasoning":"Focus TD"}}
```
Hope this helps!"""
        res = ai._extract_json_from_response(raw)
        assert res is not None
        assert res["sessions"][0]["subject_name"] == "Algorithmique"
        # total_hours was 0 -> automatically recalculated to 2.0h
        assert res["total_hours"] == 2.0

    def test_extract_json_missing_opening_brace_and_invalid_hour(self, db_session: Session):
        ai = AIService(db_session)
        # Pre-filled assistant prompt often makes LLM start directly with `"sessions": ...`
        raw = (
            '"sessions": [{"day": "Wednesday", "start_time": "24:15:00", "end_time": "25:45:00", '
            '"subject_name": "Physique", "task_type": "lecture_review", "notes": "Solve problems 7.3-8.16"}], '
            '"reasoning": "Test"'
        )
        res = ai._extract_json_from_response(raw)
        assert res is not None
        sess = res["sessions"][0]
        # 24:15:00 -> 00:15:00 and 25:45:00 -> 01:45:00
        assert sess["start_time"] == "00:15:00"
        assert sess["end_time"] == "01:45:00"
        # Vague note "Solve problems 7.3-8.16" enriched automatically
        assert "Solve problems 7.3-8.16" not in sess["notes"]


class TestFallbackPlanAndStreamResilience:
    """Tests that when Colab/Ollama is down, both batch and SSE stream return a valid fallback plan."""

    def test_generate_fallback_plan_structure(self, db_session: Session):
        ai = AIService(db_session)
        data = _sample_planning_data(num_subjects=4, num_slots_per_day=2)
        plan = ai._generate_fallback_plan(data, weekly_study_goal=6.0, language="fr")

        assert "sessions" in plan
        assert len(plan["sessions"]) >= 4
        assert plan["total_hours"] > 0
        allowed_days = {"Monday", "Wednesday", "Friday"}
        for s in plan["sessions"]:
            assert s["day"] in allowed_days
            assert s["notes"]

    @pytest.mark.asyncio
    async def test_stream_falls_back_when_remote_ai_fails(self, db_session: Session, test_user: User):
        ai = AIService(db_session)
        ai.use_colab = True
        data = _sample_planning_data(num_subjects=3, num_slots_per_day=2)

        # Force _call_colab_api to fail and stream POST to raise ConnectError
        with patch("httpx.AsyncClient.stream", side_effect=Exception("Colab offline")), \
             patch.object(ai, "_call_colab_api", new=AsyncMock(side_effect=Exception("Colab offline"))):
            events = []
            async for chunk in ai.generate_study_plan_stream(
                planning_data=data,
                weekly_study_goal=6.0,
                user_preferences={},
                user_id=test_user.id,
                language="fr",
            ):
                if chunk.startswith("data:"):
                    events.append(json.loads(chunk[len("data:"):].strip()))

        event_types = [e["type"] for e in events]
        assert "done" in event_types
        assert "error" not in event_types
        done_evt = next(e for e in events if e["type"] == "done")
        assert done_evt.get("fallback") is True
        assert len(done_evt["plan"]["sessions"]) > 0

