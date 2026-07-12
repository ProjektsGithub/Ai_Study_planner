"""
Grade Service
=============

Handles grade creation, updates, validation status calculation,
and triggers ECTS recalculation when a course becomes validated.

Validation logic (Requirement 2.3–2.6):
    grade_obtained is None  → in_progress
    grade_obtained >= min   → validated
    grade_obtained < min    → failed
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.grade import Grade
from app.schemas.grade import GradeCreate, GradeUpdate, ValidationStatus

logger = logging.getLogger(__name__)


class GradeService:
    """Manages course grades with automatic validation status calculation."""

    # ------------------------------------------------------------------
    # Validation status calculation
    # ------------------------------------------------------------------

    def calculate_validation_status(
        self,
        grade_obtained: Optional[float],
        min_passing_grade: float,
    ) -> str:
        """
        Determine validation status from grade value.

        Returns:
            'in_progress' — no grade entered
            'validated'   — grade_obtained >= min_passing_grade
            'failed'      — grade_obtained < min_passing_grade

        Requirements: 2.3, 2.4, 2.5, 2.6
        """
        if grade_obtained is None:
            return ValidationStatus.IN_PROGRESS.value
        if grade_obtained >= min_passing_grade:
            return ValidationStatus.VALIDATED.value
        return ValidationStatus.FAILED.value

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_or_update_grade(
        self,
        db: Session,
        user_id: int,
        grade_data: GradeCreate,
    ) -> Grade:
        """
        Create a new grade entry or update an existing one for the same
        (user_id, course_id, attempt_number) combination.

        Automatically calculates validation_status.
        Triggers ECTS recalculation if status changes to 'validated'.

        Requirements: 2.1, 2.2, 2.7, 2.8, 2.9
        """
        existing = (
            db.query(Grade)
            .filter(
                Grade.user_id == user_id,
                Grade.course_id == grade_data.course_id,
                Grade.attempt_number == grade_data.attempt_number,
            )
            .first()
        )

        new_status = self.calculate_validation_status(
            grade_data.grade_obtained, grade_data.min_passing_grade
        )

        if existing:
            old_status = existing.validation_status
            existing.course_name = grade_data.course_name
            existing.grade_obtained = grade_data.grade_obtained
            existing.min_passing_grade = grade_data.min_passing_grade
            existing.max_grade = grade_data.max_grade
            existing.validation_status = new_status
            existing.semester = grade_data.semester
            existing.ects_credits = grade_data.ects_credits
            existing.coefficient = grade_data.coefficient
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)

            # Trigger ECTS recalculation if status changed to validated
            if old_status != ValidationStatus.VALIDATED.value and new_status == ValidationStatus.VALIDATED.value:
                self._trigger_ects_recalculation(db, user_id)

            logger.info(
                "[GradeService] Updated grade for user=%d course=%d attempt=%d status=%s",
                user_id, grade_data.course_id, grade_data.attempt_number, new_status,
            )
            return existing

        # Create new grade entry
        now = datetime.utcnow()
        grade = Grade(
            user_id=user_id,
            course_id=grade_data.course_id,
            course_name=grade_data.course_name,
            grade_obtained=grade_data.grade_obtained,
            min_passing_grade=grade_data.min_passing_grade,
            max_grade=grade_data.max_grade,
            validation_status=new_status,
            attempt_number=grade_data.attempt_number,
            semester=grade_data.semester,
            ects_credits=grade_data.ects_credits,
            coefficient=grade_data.coefficient,
            created_at=now,
            updated_at=now,
        )
        db.add(grade)
        db.commit()
        db.refresh(grade)

        # Trigger ECTS recalculation if newly validated
        if new_status == ValidationStatus.VALIDATED.value:
            self._trigger_ects_recalculation(db, user_id)

        logger.info(
            "[GradeService] Created grade for user=%d course=%d attempt=%d status=%s",
            user_id, grade_data.course_id, grade_data.attempt_number, new_status,
        )
        return grade

    def update_grade(
        self,
        db: Session,
        grade_id: int,
        user_id: int,
        grade_data: GradeUpdate,
    ) -> Grade:
        """
        Update an existing grade by its ID, with ownership check.

        Requirements: 2.8
        """
        grade = (
            db.query(Grade)
            .filter(Grade.id == grade_id, Grade.user_id == user_id)
            .first()
        )
        if grade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grade with id={grade_id} not found for this user",
            )

        update_dict = grade_data.model_dump(exclude_none=True)
        old_status = grade.validation_status

        # Apply field updates
        for field, value in update_dict.items():
            setattr(grade, field, value)

        # Recalculate validation status with updated values
        grade.validation_status = self.calculate_validation_status(
            grade.grade_obtained, grade.min_passing_grade
        )
        grade.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(grade)

        # Trigger ECTS recalculation if status changed to validated
        if (old_status != ValidationStatus.VALIDATED.value
                and grade.validation_status == ValidationStatus.VALIDATED.value):
            self._trigger_ects_recalculation(db, user_id)

        return grade

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_grades_by_user(self, db: Session, user_id: int) -> List[Grade]:
        """
        Retrieve all grades for a student (latest attempt per course).

        Requirements: 2.1
        """
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id)
            .order_by(Grade.course_id, Grade.attempt_number.desc())
            .all()
        )

    def get_grade_history(
        self, db: Session, user_id: int, course_id: int
    ) -> List[Grade]:
        """
        Retrieve all attempts for a specific course (grade history).

        Requirements: 2.9
        """
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.course_id == course_id)
            .order_by(Grade.attempt_number)
            .all()
        )

    def get_grade_by_id(
        self, db: Session, grade_id: int, user_id: int
    ) -> Grade:
        """Get a single grade by ID, enforcing ownership."""
        grade = (
            db.query(Grade)
            .filter(Grade.id == grade_id, Grade.user_id == user_id)
            .first()
        )
        if grade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grade with id={grade_id} not found for this user",
            )
        return grade

    def get_failed_grades(self, db: Session, user_id: int) -> List[Grade]:
        """Return only failed grades for a student."""
        return (
            db.query(Grade)
            .filter(
                Grade.user_id == user_id,
                Grade.validation_status == ValidationStatus.FAILED.value,
            )
            .order_by(Grade.course_id)
            .all()
        )

    # ------------------------------------------------------------------
    # ECTS trigger
    # ------------------------------------------------------------------

    def _trigger_ects_recalculation(self, db: Session, user_id: int) -> None:
        """
        Trigger ECTS progression recalculation.
        Imported lazily to avoid circular imports.

        Requirements: 3.7
        """
        try:
            from app.services.ects_service import ects_service
            ects_service.calculate_progression(db, user_id)
        except Exception as exc:
            # Non-fatal: log and continue
            logger.warning(
                "[GradeService] ECTS recalculation trigger failed for user=%d: %s",
                user_id, exc,
            )


# Module-level singleton
grade_service = GradeService()
