"""
ECTS Service
============

Calculates ECTS progression (obtained, required, remaining, percentage)
for a student based on their validated grades and their cursus from the
Super Admin Platform.

All returned float values are rounded to 2 decimal places (Requirement 3.8).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.ects_progress import ECTSProgress
from app.models.grade import Grade
from app.schemas.ects_progress import (
    ECTSProgressionResponse,
    ECTSSemesterBreakdown,
    ECTSProgressWithBreakdown,
)
from app.schemas.grade import ValidationStatus
import app.services.super_admin_client as client

logger = logging.getLogger(__name__)


class ECTSService:
    """Calculates and caches ECTS progression for students."""

    # ------------------------------------------------------------------
    # Core calculations
    # ------------------------------------------------------------------

    def calculate_ects_obtained(self, db: Session, user_id: int) -> float:
        """
        Sum ECTS credits from all validated courses for a student.

        Requirements: 3.1
        """
        validated_grades = (
            db.query(Grade)
            .filter(
                Grade.user_id == user_id,
                Grade.validation_status == ValidationStatus.VALIDATED.value,
                Grade.ects_credits.isnot(None),
            )
            .all()
        )
        total = sum(g.ects_credits for g in validated_grades if g.ects_credits)
        return round(total, 2)

    def get_ects_required(self, db: Session, cursus_id: int) -> Optional[float]:
        """
        Fetch total ECTS required for graduation from Super Admin Platform.

        Requirements: 3.2
        """
        total = client.fetch_total_ects_for_cursus(db, cursus_id)
        return round(total, 2) if total is not None else None

    def calculate_progression(
        self, db: Session, user_id: int
    ) -> ECTSProgressionResponse:
        """
        Calculate full ECTS progression and persist result.

        Returns:
            ECTSProgressionResponse with 2-decimal precision on all floats.

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.7, 3.8
        """
        from app.models.student_profile import StudentProfile

        # Fetch student cursus_id to get required ECTS
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user_id)
            .first()
        )
        cursus_id = profile.cursus_id if profile else None

        ects_obtained = self.calculate_ects_obtained(db, user_id)
        ects_required = 0.0
        if cursus_id:
            req = self.get_ects_required(db, cursus_id)
            ects_required = req if req is not None else 0.0

        ects_remaining = max(0.0, ects_required - ects_obtained)
        progression_percentage = (
            round((ects_obtained / ects_required) * 100, 2)
            if ects_required > 0
            else 0.0
        )

        # Persist / update the cached ECTSProgress record
        now = datetime.utcnow()
        record = (
            db.query(ECTSProgress)
            .filter(ECTSProgress.user_id == user_id)
            .first()
        )
        if record:
            record.ects_obtained = ects_obtained
            record.ects_required = ects_required
            record.ects_remaining = round(ects_remaining, 2)
            record.progression_percentage = progression_percentage
            record.last_calculated_at = now
        else:
            record = ECTSProgress(
                user_id=user_id,
                ects_obtained=ects_obtained,
                ects_required=ects_required,
                ects_remaining=round(ects_remaining, 2),
                progression_percentage=progression_percentage,
                last_calculated_at=now,
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        logger.info(
            "[ECTSService] Progression for user=%d: %.2f/%.2f (%.2f%%)",
            user_id, ects_obtained, ects_required, progression_percentage,
        )
        return ECTSProgressionResponse(
            user_id=user_id,
            ects_obtained=ects_obtained,
            ects_required=ects_required,
            ects_remaining=round(ects_remaining, 2),
            progression_percentage=progression_percentage,
            last_calculated_at=now,
        )

    def get_progression(self, db: Session, user_id: int) -> ECTSProgressionResponse:
        """
        Return the stored ECTSProgress record (recalculate if missing).

        Requirements: 3.1–3.4, 3.8
        """
        record = (
            db.query(ECTSProgress)
            .filter(ECTSProgress.user_id == user_id)
            .first()
        )
        if record is None:
            # No stored record — calculate fresh
            return self.calculate_progression(db, user_id)

        return ECTSProgressionResponse(
            user_id=user_id,
            ects_obtained=round(record.ects_obtained, 2),
            ects_required=round(record.ects_required, 2),
            ects_remaining=round(record.ects_remaining, 2),
            progression_percentage=round(record.progression_percentage, 2),
            last_calculated_at=record.last_calculated_at,
        )

    # ------------------------------------------------------------------
    # Semester breakdown
    # ------------------------------------------------------------------

    def calculate_ects_per_semester(
        self, db: Session, user_id: int
    ) -> List[ECTSSemesterBreakdown]:
        """
        Calculate ECTS obtained and remaining per semester.

        Groups validated grades by semester column and calculates
        the breakdown.

        Requirements: 3.5, 3.6
        """
        all_grades = (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.semester.isnot(None))
            .all()
        )

        # Group grades by semester
        by_semester: Dict[int, List[Grade]] = {}
        for g in all_grades:
            if g.semester is not None:
                by_semester.setdefault(g.semester, []).append(g)

        breakdown: List[ECTSSemesterBreakdown] = []
        for sem_num in sorted(by_semester.keys()):
            grades = by_semester[sem_num]
            ects_obtained = round(
                sum(
                    g.ects_credits
                    for g in grades
                    if g.validation_status == ValidationStatus.VALIDATED.value
                    and g.ects_credits
                ),
                2,
            )
            ects_total = round(
                sum(g.ects_credits for g in grades if g.ects_credits), 2
            )
            ects_remaining = round(max(0.0, ects_total - ects_obtained), 2)
            progression = (
                round((ects_obtained / ects_total) * 100, 2)
                if ects_total > 0
                else 0.0
            )
            breakdown.append(
                ECTSSemesterBreakdown(
                    semester=sem_num,
                    ects_obtained=ects_obtained,
                    ects_required=ects_total,
                    ects_remaining=ects_remaining,
                    progression_percentage=progression,
                )
            )
        return breakdown

    def get_full_progression(self, db: Session, user_id: int) -> ECTSProgressWithBreakdown:
        """Return ECTS progression with per-semester breakdown."""
        base = self.get_progression(db, user_id)
        breakdown = self.calculate_ects_per_semester(db, user_id)
        return ECTSProgressWithBreakdown(
            **base.model_dump(),
            semester_breakdown=breakdown,
        )


# Module-level singleton
ects_service = ECTSService()
