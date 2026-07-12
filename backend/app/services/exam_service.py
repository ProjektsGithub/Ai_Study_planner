"""
Exam Service
============

Manages exam CRUD operations with ownership checks and countdown calculation.

Requirements: 5.1–5.8
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.exam import Exam
from app.schemas.exam import ExamCreate, ExamUpdate, ExamWithCountdown

logger = logging.getLogger(__name__)


class ExamService:
    """Manages exam scheduling and countdown tracking."""

    # ------------------------------------------------------------------
    # Countdown
    # ------------------------------------------------------------------

    def calculate_days_until_exam(self, exam_date: date) -> int:
        """
        Calculate days until exam. Returns negative if exam is in the past.

        Requirements: 5.3, 5.4
        """
        return (exam_date - date.today()).days

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_exam(
        self, db: Session, user_id: int, exam_data: ExamCreate
    ) -> Exam:
        """
        Create a new exam entry for a student.

        Requirements: 5.1, 5.2, 5.5, 5.6
        """
        now = datetime.utcnow()
        exam = Exam(
            user_id=user_id,
            course_id=exam_data.course_id,
            course_name=exam_data.course_name,
            exam_date=exam_data.exam_date,
            exam_time=exam_data.exam_time,
            location=exam_data.location,
            exam_type=exam_data.exam_type.value if exam_data.exam_type else None,
            weight=exam_data.weight,
            notes=exam_data.notes,
            created_at=now,
            updated_at=now,
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        logger.info(
            "[ExamService] Created exam for user=%d course=%d date=%s",
            user_id, exam_data.course_id, exam_data.exam_date,
        )
        return exam

    def update_exam(
        self, db: Session, exam_id: int, user_id: int, exam_data: ExamUpdate
    ) -> Exam:
        """
        Update an existing exam with ownership check.

        Requirements: 5.5
        """
        exam = self._get_owned_exam(db, exam_id, user_id)

        update_dict = exam_data.model_dump(exclude_none=True)
        for field, value in update_dict.items():
            if field == "exam_type" and value is not None:
                setattr(exam, field, value.value if hasattr(value, "value") else value)
            else:
                setattr(exam, field, value)
        exam.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(exam)

        logger.info("[ExamService] Updated exam id=%d for user=%d", exam_id, user_id)
        return exam

    def delete_exam(self, db: Session, exam_id: int, user_id: int) -> None:
        """
        Delete an exam with ownership check.

        Requirements: 5.5
        """
        exam = self._get_owned_exam(db, exam_id, user_id)
        db.delete(exam)
        db.commit()
        logger.info("[ExamService] Deleted exam id=%d for user=%d", exam_id, user_id)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_upcoming_exams(
        self, db: Session, user_id: int
    ) -> List[ExamWithCountdown]:
        """
        Retrieve all future exams sorted by date ascending with countdown.

        Requirements: 5.7, 5.8
        """
        today = date.today()
        exams = (
            db.query(Exam)
            .filter(Exam.user_id == user_id, Exam.exam_date >= today)
            .order_by(Exam.exam_date.asc())
            .all()
        )
        return [self._to_countdown(e) for e in exams]

    def get_all_exams(
        self, db: Session, user_id: int
    ) -> List[ExamWithCountdown]:
        """
        Retrieve all exams (including past) with countdown (negative for past).
        """
        exams = (
            db.query(Exam)
            .filter(Exam.user_id == user_id)
            .order_by(Exam.exam_date.asc())
            .all()
        )
        return [self._to_countdown(e) for e in exams]

    def get_exams_by_course(
        self, db: Session, user_id: int, course_id: int
    ) -> List[ExamWithCountdown]:
        """Return all exams for a specific course."""
        exams = (
            db.query(Exam)
            .filter(Exam.user_id == user_id, Exam.course_id == course_id)
            .order_by(Exam.exam_date.asc())
            .all()
        )
        return [self._to_countdown(e) for e in exams]

    def get_next_exam_for_course(
        self, db: Session, user_id: int, course_id: int
    ) -> ExamWithCountdown | None:
        """Return the next upcoming exam for a course (used by risk/priority services)."""
        today = date.today()
        exam = (
            db.query(Exam)
            .filter(
                Exam.user_id == user_id,
                Exam.course_id == course_id,
                Exam.exam_date >= today,
            )
            .order_by(Exam.exam_date.asc())
            .first()
        )
        if exam is None:
            return None
        return self._to_countdown(exam)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_owned_exam(self, db: Session, exam_id: int, user_id: int) -> Exam:
        """Fetch exam by ID and enforce ownership."""
        exam = (
            db.query(Exam)
            .filter(Exam.id == exam_id, Exam.user_id == user_id)
            .first()
        )
        if exam is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam with id={exam_id} not found for this user",
            )
        return exam

    def _to_countdown(self, exam: Exam) -> ExamWithCountdown:
        """Convert an Exam ORM object to ExamWithCountdown schema."""
        return ExamWithCountdown(
            id=exam.id,
            user_id=exam.user_id,
            course_id=exam.course_id,
            course_name=exam.course_name,
            exam_date=exam.exam_date,
            exam_time=exam.exam_time,
            location=exam.location,
            exam_type=exam.exam_type,
            weight=exam.weight,
            notes=exam.notes,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            days_until=self.calculate_days_until_exam(exam.exam_date),
        )


# Module-level singleton
exam_service = ExamService()
