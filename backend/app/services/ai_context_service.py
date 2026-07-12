"""
AI Context Service
==================

Builds the complete AI context JSON payload for Llama + LoRA study plan
generation. Aggregates data from all academic tracking services.

Structure follows design.md §8:
    student_profile     ← AcademicProfileService
    academic_progress   ← ECTSService
    failed_courses      ← FailedCourseService
    course_priorities   ← PriorityService + RiskAnalysisService
    availability_slots  ← existing Availability model
    constraints         ← existing Constraint model
    upcoming_exams      ← ExamService
    generated_at        ← ISO 8601 timestamp

Requirements: 13.1–13.14
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.ai_context import (
    AIContextResponse,
    AIContextRequest,
    AIStudentProfile,
    AIAcademicProgress,
    AIFailedCourse,
    AICoursePriority,
    AIAvailabilitySlot,
    AIConstraint,
    AIUpcomingExam,
)

logger = logging.getLogger(__name__)


class AIContextService:
    """Assembles the full AI context payload for the study plan generator."""

    def build_context(
        self,
        db: Session,
        user_id: int,
        request: AIContextRequest | None = None,
    ) -> AIContextResponse:
        """
        Build the complete AI context for a student.

        Aggregates data from all services and resolves names from Super Admin
        Platform (cached). All floats are 2-decimal precision.

        Requirements: 13.1–13.14
        """
        if request is None:
            request = AIContextRequest()

        logger.info("[AIContextService] Building AI context for user_id=%d", user_id)

        # 1. Student academic profile
        student_profile_section = self._build_student_profile(db, user_id)

        # 2. ECTS progression
        academic_progress_section = self._build_academic_progress(db, user_id)

        # 3. Failed courses
        failed_courses_section = self._build_failed_courses(db, user_id)

        # 4. Course priorities + risk (merged)
        course_priorities_section = self._build_course_priorities(
            db, user_id, request.include_priority_factors
        )

        # 5. Availability slots (existing model)
        availability_section = self._build_availability_slots(db, user_id)

        # 6. Constraints (existing model)
        constraints_section = self._build_constraints(db, user_id)

        # 7. Upcoming exams with countdown
        exams_section = self._build_upcoming_exams(db, user_id)

        return AIContextResponse(
            student_profile=student_profile_section,
            academic_progress=academic_progress_section,
            failed_courses=failed_courses_section,
            course_priorities=course_priorities_section,
            availability_slots=availability_section,
            constraints=constraints_section,
            upcoming_exams=exams_section,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_student_profile(self, db: Session, user_id: int) -> AIStudentProfile:
        """Requirements: 13.2"""
        try:
            from app.services.academic_profile_service import academic_profile_service
            profile = academic_profile_service.get_academic_profile(db, user_id)
            return AIStudentProfile(
                university_id=profile.university_id,
                university_name=profile.university_name,
                filiere_id=profile.filiere_id,
                filiere_name=profile.filiere_name,
                cursus_id=profile.cursus_id,
                cursus_name=profile.cursus_name,
                current_semester=profile.current_semester,
                academic_year=profile.academic_year,
            )
        except HTTPException:
            return AIStudentProfile()
        except Exception as exc:
            logger.warning("[AIContextService] student_profile error: %s", exc)
            return AIStudentProfile()

    def _build_academic_progress(self, db: Session, user_id: int) -> AIAcademicProgress:
        """Requirements: 13.3"""
        try:
            from app.services.ects_service import ects_service
            progress = ects_service.get_progression(db, user_id)
            return AIAcademicProgress(
                ects_obtained=progress.ects_obtained,
                ects_required=progress.ects_required,
                ects_remaining=progress.ects_remaining,
                progression_percentage=progress.progression_percentage,
            )
        except Exception as exc:
            logger.warning("[AIContextService] academic_progress error: %s", exc)
            return AIAcademicProgress(
                ects_obtained=0.0,
                ects_required=0.0,
                ects_remaining=0.0,
                progression_percentage=0.0,
            )

    def _build_failed_courses(self, db: Session, user_id: int) -> List[AIFailedCourse]:
        """Requirements: 13.4"""
        try:
            from app.services.failed_course_service import failed_course_service
            failed = failed_course_service.get_failed_courses(db, user_id)
            return [
                AIFailedCourse(
                    course_id=fc.course_id,
                    course_name=fc.course_name,
                    original_semester=fc.original_semester,
                    attempt_count=fc.attempt_count,
                    days_since_first_failure=fc.days_since_first_failure,
                    is_prerequisite_blocker=fc.is_prerequisite_blocker,
                    blocks_courses=fc.blocks_courses,
                )
                for fc in failed
            ]
        except Exception as exc:
            logger.warning("[AIContextService] failed_courses error: %s", exc)
            try: db.rollback()
            except Exception: pass
            return []

    def _build_course_priorities(
        self, db: Session, user_id: int, include_factors: bool
    ) -> List[AICoursePriority]:
        """Requirements: 13.5"""
        try:
            from app.services.priority_service import priority_service
            priorities = priority_service.calculate_all_priorities(db, user_id)
            result: List[AICoursePriority] = []
            for p in priorities:
                result.append(
                    AICoursePriority(
                        course_id=p.course_id,
                        course_name=p.course_name or f"Course {p.course_id}",
                        priority_score=p.priority_score,
                        risk_level=p.risk_level.value if p.risk_level else "medium",
                        recommended_weekly_hours=p.recommended_weekly_hours,
                        success_probability=p.success_probability,
                    )
                )
            return result
        except Exception as exc:
            logger.warning("[AIContextService] course_priorities error: %s", exc)
            try: db.rollback()
            except Exception: pass
            return []

    def _build_availability_slots(
        self, db: Session, user_id: int
    ) -> List[AIAvailabilitySlot]:
        """Requirements: 13.6"""
        try:
            from app.models.availability import Availability
            slots = (
                db.query(Availability)
                .filter(Availability.user_id == user_id)
                .order_by(Availability.day_of_week, Availability.start_time)
                .all()
            )
            return [
                AIAvailabilitySlot(
                    day=slot.day_of_week,
                    start_time=str(slot.start_time),
                    end_time=str(slot.end_time),
                    energy_level=slot.energy_level,
                )
                for slot in slots
            ]
        except Exception as exc:
            logger.warning("[AIContextService] availability_slots error: %s", exc)
            try: db.rollback()
            except Exception: pass
            return []

    def _build_constraints(self, db: Session, user_id: int) -> List[AIConstraint]:
        """Requirements: 13.7"""
        try:
            from app.models.constraint import Constraint
            constraints = (
                db.query(Constraint)
                .filter(Constraint.user_id == user_id)
                .all()
            )
            result: List[AIConstraint] = []
            for c in constraints:
                constraint_type = getattr(c, "constraint_type", None) or "other"
                schedule = getattr(c, "schedule", None) or getattr(c, "description", None)
                active = getattr(c, "is_active", True)
                result.append(
                    AIConstraint(
                        type=constraint_type,
                        schedule=schedule,
                        active=active,
                    )
                )
            return result
        except Exception as exc:
            logger.warning("[AIContextService] constraints error: %s", exc)
            try: db.rollback()
            except Exception: pass
            return []

    def _build_upcoming_exams(self, db: Session, user_id: int) -> List[AIUpcomingExam]:
        """Requirements: 13.8"""
        try:
            from app.services.exam_service import exam_service
            exams = exam_service.get_upcoming_exams(db, user_id)
            return [
                AIUpcomingExam(
                    course_id=e.course_id,
                    course_name=e.course_name,
                    exam_date=e.exam_date.isoformat(),
                    exam_time=str(e.exam_time) if e.exam_time else None,
                    location=e.location,
                    exam_type=e.exam_type,
                    weight=e.weight,
                    days_until=e.days_until,
                )
                for e in exams
            ]
        except Exception as exc:
            logger.warning("[AIContextService] upcoming_exams error: %s", exc)
            try: db.rollback()
            except Exception: pass
            return []


# Module-level singleton
ai_context_service = AIContextService()
