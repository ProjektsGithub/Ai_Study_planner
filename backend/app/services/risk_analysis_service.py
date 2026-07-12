"""
Risk Analysis Service
=====================

Calculates academic risk scores for courses and estimates success probability.

Risk level logic (Requirements 8.2–8.7):
    HIGH   — validation_status='failed'
           — grade < (min_passing - 20% of min_passing)
    MEDIUM — grade 0–20% below min_passing
           — exam within 7 days AND progress < 70%
    LOW    — grade > min_passing
           — progress > 80% AND exam > 14 days away
    DEFAULT → MEDIUM

Success probability (Requirements 12.1–12.8):
    grade >= min + 10%  → 90–100%
    grade 0 to +10%     → 70–90%
    grade 0 to -10%     → 40–70%
    grade < -10%        → 10–40%
    -10% per failed attempt
    +5%  when recommended hours are being met
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.grade import Grade
from app.models.risk_score import RiskScore
from app.schemas.analysis import RiskLevel, RiskScoreResponse
from app.schemas.grade import ValidationStatus

logger = logging.getLogger(__name__)


class RiskAnalysisService:
    """Calculates risk scores and success probabilities for enrolled courses."""

    # ------------------------------------------------------------------
    # Risk score calculation
    # ------------------------------------------------------------------

    def calculate_risk_score(
        self, db: Session, user_id: int, course_id: int
    ) -> RiskScoreResponse:
        """
        Calculate risk level for a single course.
        Persists result to risk_scores table.

        Requirements: 8.1–8.8, 19.2
        """
        grade = self._get_latest_grade(db, user_id, course_id)
        exam_days = self._get_days_until_exam(db, user_id, course_id)
        attempt_count = self._get_attempt_count(db, user_id, course_id)
        failed_course_ids = self._get_failed_course_ids(db, user_id)
        is_blocker = self._is_prerequisite_blocker(db, course_id)

        risk_level, factors = self._compute_risk_level(
            grade=grade,
            exam_days=exam_days,
            attempt_count=attempt_count,
            is_blocker=is_blocker,
            failed_course_ids=failed_course_ids,
            course_id=course_id,
        )

        # Persist / upsert risk score
        record = (
            db.query(RiskScore)
            .filter(RiskScore.user_id == user_id, RiskScore.course_id == course_id)
            .first()
        )
        now = datetime.utcnow()
        if record:
            record.risk_level = risk_level
            record.factors = factors
            record.calculated_at = now
        else:
            record = RiskScore(
                user_id=user_id,
                course_id=course_id,
                risk_level=risk_level,
                factors=factors,
                calculated_at=now,
            )
            db.add(record)
        db.commit()
        db.refresh(record)

        # Resolve course name
        course_name = grade.course_name if grade else None

        return RiskScoreResponse(
            id=record.id,
            user_id=user_id,
            course_id=course_id,
            course_name=course_name,
            risk_level=RiskLevel(risk_level),
            factors=factors,
            calculated_at=record.calculated_at,
        )

    def calculate_all_risk_scores(
        self, db: Session, user_id: int
    ) -> List[RiskScoreResponse]:
        """
        Calculate risk scores for all courses a student has grades for.
        Returns list sorted HIGH → MEDIUM → LOW.

        Requirements: 8.1, 19.2
        """
        # Get all unique course_ids for this student
        course_ids = (
            db.query(Grade.course_id)
            .filter(Grade.user_id == user_id)
            .distinct()
            .all()
        )
        course_ids = [row[0] for row in course_ids]

        results: List[RiskScoreResponse] = []
        for cid in course_ids:
            try:
                score = self.calculate_risk_score(db, user_id, cid)
                results.append(score)
            except Exception as exc:
                logger.warning(
                    "[RiskAnalysisService] Failed to calculate risk for user=%d course=%d: %s",
                    user_id, cid, exc,
                )

        # Sort: high first, then medium, then low
        level_order = {
            RiskLevel.HIGH: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.LOW: 2,
        }
        results.sort(key=lambda r: level_order.get(r.risk_level, 1))
        return results

    # ------------------------------------------------------------------
    # Success probability estimation (Task 13.1)
    # ------------------------------------------------------------------

    def estimate_success_probability(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        recommended_hours: Optional[float] = None,
        actual_hours_met: bool = False,
    ) -> float:
        """
        Estimate the probability (0–100%) of passing a course.

        Formula:
            Base from grade vs min_passing thresholds:
                grade >= min + 10%  → base in [90, 100]
                grade in [min, min+10%[  → base in [70, 90]
                grade in [min-10%, min[  → base in [40, 70]
                grade < min - 10%   → base in [10, 40]
            Adjustments:
                -10% per failed attempt (Req 12.7)
                +5%  if recommended hours are being met (Req 12.8)
            Clamped to [0, 100].

        Requirements: 12.1–12.8
        """
        grade = self._get_latest_grade(db, user_id, course_id)
        attempt_count = self._get_attempt_count(db, user_id, course_id)

        if grade is None or grade.grade_obtained is None:
            # No grade data — default medium probability
            base = 50.0
        else:
            g = grade.grade_obtained
            mn = grade.min_passing_grade
            ten_pct = mn * 0.10

            if g >= mn + ten_pct:
                # Interpolate within [90, 100]
                excess = g - (mn + ten_pct)
                max_excess = mn  # rough upper bound
                base = 90.0 + min(10.0, (excess / max(max_excess, 1)) * 10)
            elif g >= mn:
                # Interpolate within [70, 90]
                ratio = (g - mn) / max(ten_pct, 0.01)
                base = 70.0 + ratio * 20.0
            elif g >= mn - ten_pct:
                # Interpolate within [40, 70]
                ratio = (g - (mn - ten_pct)) / max(ten_pct, 0.01)
                base = 40.0 + ratio * 30.0
            else:
                # Interpolate within [10, 40]
                deficit = mn - ten_pct - g
                max_deficit = mn  # rough scale
                base = max(10.0, 40.0 - (deficit / max(max_deficit, 1)) * 30.0)

        # Reduce by 10% per failed attempt (prior attempts, not current)
        prior_failures = max(0, attempt_count - 1)
        base -= prior_failures * 10.0

        # Increase by 5% if recommended study hours are being met
        if actual_hours_met:
            base += 5.0

        probability = round(min(100.0, max(0.0, base)), 2)
        logger.debug(
            "[RiskAnalysisService] Success probability user=%d course=%d: %.2f%%",
            user_id, course_id, probability,
        )
        return probability

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_risk_level(
        self,
        grade: Optional[Grade],
        exam_days: Optional[int],
        attempt_count: int,
        is_blocker: bool,
        failed_course_ids: set,
        course_id: int,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Apply risk rules from design.md §6 and return (risk_level, factors_dict).

        Requirements: 8.2–8.7
        """
        factors: Dict[str, Any] = {
            "grade_obtained": grade.grade_obtained if grade else None,
            "min_passing_grade": grade.min_passing_grade if grade else None,
            "days_until_exam": exam_days,
            "attempt_count": attempt_count,
            "is_prerequisite_blocker": is_blocker,
        }

        # --- HIGH risk conditions ---

        # 1. Already marked failed
        if grade and grade.validation_status == ValidationStatus.FAILED.value:
            factors["reason"] = "validation_status_failed"
            return RiskLevel.HIGH.value, factors

        # 2. Grade > 20% below min_passing
        if grade and grade.grade_obtained is not None:
            mn = grade.min_passing_grade
            threshold_high = mn - (0.20 * mn)  # 80% of min
            if grade.grade_obtained < threshold_high:
                factors["reason"] = "grade_more_than_20pct_below_min"
                return RiskLevel.HIGH.value, factors

        # --- MEDIUM risk conditions ---

        # 3. Grade 0–20% below min_passing
        if grade and grade.grade_obtained is not None:
            mn = grade.min_passing_grade
            threshold_high = mn - (0.20 * mn)
            if threshold_high <= grade.grade_obtained < mn:
                factors["reason"] = "grade_0_to_20pct_below_min"
                return RiskLevel.MEDIUM.value, factors

        # 4. Exam within 7 days AND progress < 70%
        if exam_days is not None and exam_days <= 7:
            progress = self._estimate_progress(grade)
            factors["estimated_progress"] = progress
            if progress < 70.0:
                factors["reason"] = "exam_within_7_days_low_progress"
                return RiskLevel.MEDIUM.value, factors

        # 5. Multiple failed attempts even if current is in_progress
        if attempt_count >= 2:
            factors["reason"] = "multiple_attempts"
            return RiskLevel.MEDIUM.value, factors

        # --- LOW risk conditions ---

        # 6. Grade above min_passing
        if grade and grade.grade_obtained is not None and grade.grade_obtained >= grade.min_passing_grade:
            factors["reason"] = "grade_above_min"
            return RiskLevel.LOW.value, factors

        # 7. Progress > 80% AND exam > 14 days away
        if exam_days is not None and exam_days > 14:
            progress = self._estimate_progress(grade)
            factors["estimated_progress"] = progress
            if progress > 80.0:
                factors["reason"] = "good_progress_exam_distant"
                return RiskLevel.LOW.value, factors

        # Default → MEDIUM
        factors["reason"] = "default_medium"
        return RiskLevel.MEDIUM.value, factors

    def _estimate_progress(self, grade: Optional[Grade]) -> float:
        """
        Estimate study progress as a percentage based on grade ratio.
        If no grade, return 0.
        """
        if grade is None or grade.grade_obtained is None:
            return 0.0
        if grade.max_grade and grade.max_grade > 0:
            return round((grade.grade_obtained / grade.max_grade) * 100, 2)
        return 0.0

    def _get_latest_grade(
        self, db: Session, user_id: int, course_id: int
    ) -> Optional[Grade]:
        """Return the most recent grade attempt for a course."""
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.course_id == course_id)
            .order_by(Grade.attempt_number.desc())
            .first()
        )

    def _get_attempt_count(
        self, db: Session, user_id: int, course_id: int
    ) -> int:
        """Return total number of grade attempts for a course."""
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.course_id == course_id)
            .count()
        )

    def _get_days_until_exam(
        self, db: Session, user_id: int, course_id: int
    ) -> Optional[int]:
        """Return days until next exam for this course (None if no exam scheduled)."""
        try:
            from app.services.exam_service import exam_service
            exam = exam_service.get_next_exam_for_course(db, user_id, course_id)
            return exam.days_until if exam else None
        except Exception:
            return None

    def _get_failed_course_ids(self, db: Session, user_id: int) -> set:
        """Return set of course_ids currently marked as failed."""
        try:
            from app.services.failed_course_service import failed_course_service
            return failed_course_service.get_failed_course_ids(db, user_id)
        except Exception:
            return set()

    def _is_prerequisite_blocker(self, db: Session, course_id: int) -> bool:
        """Return True if this course is a prerequisite for any other course."""
        try:
            import app.services.super_admin_client as client
            prereq_map = client.fetch_prerequisite_map(db)
            # prereq_map: {course_id: [list of prereq_ids]}
            # We need to check if course_id appears as a VALUE (prerequisite of another)
            for prereq_ids in prereq_map.values():
                if course_id in prereq_ids:
                    return True
            return False
        except Exception:
            return False


# Module-level singleton
risk_analysis_service = RiskAnalysisService()
