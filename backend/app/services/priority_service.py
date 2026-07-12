"""
Priority Service
================

Calculates course priority scores using a weighted multi-factor formula,
recommends study hours per week, and persists results to priority_scores table.

Priority formula (Requirements 9.1–9.10):
    ECTS credits      30%
    Coefficient       15%
    Exam proximity    25%
    Current grade     20%
    Difficulty level  10%
    Bonus: +15 if validation_status='failed'
    Bonus: +10 if course is a prerequisite blocker
    Normalized to 0–100

Recommended hours (Requirements 11.1–11.9):
    Base = ECTS * difficulty factor
    Increase when exam within 14 days
    Distribute proportionally by priority score
    Min 1h/week, Max 20h/week per course
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.grade import Grade
from app.models.priority_score import PriorityScore
from app.schemas.analysis import PriorityScoreResponse, RiskLevel
from app.schemas.grade import ValidationStatus

logger = logging.getLogger(__name__)

# Weights
W_ECTS = 0.30
W_COEFF = 0.15
W_EXAM = 0.25
W_GRADE = 0.20
W_DIFFICULTY = 0.10

# Bonuses
BONUS_FAILED = 15.0
BONUS_BLOCKER = 10.0

# Study hours bounds
MIN_HOURS = 1.0
MAX_HOURS = 20.0


class PriorityService:
    """Calculates priority scores and recommended study hours for enrolled courses."""

    # ------------------------------------------------------------------
    # Priority score calculation
    # ------------------------------------------------------------------

    def calculate_priority_score(
        self, db: Session, user_id: int, course_id: int
    ) -> PriorityScoreResponse:
        """
        Calculate priority score (0–100) for a single course and persist it.

        Requirements: 9.1–9.10
        """
        grade = self._get_latest_grade(db, user_id, course_id)
        course_details = self._get_course_details(db, course_id)
        exam_days = self._get_days_until_exam(db, user_id, course_id)
        is_failed = grade and grade.validation_status == ValidationStatus.FAILED.value
        is_blocker = self._is_prerequisite_blocker(db, course_id)
        attempt_count = self._get_attempt_count(db, user_id, course_id)

        score, factors = self._compute_priority(
            grade=grade,
            course_details=course_details,
            exam_days=exam_days,
            is_failed=is_failed,
            is_blocker=is_blocker,
        )

        recommended_hours = self.calculate_recommended_hours(
            db=db,
            user_id=user_id,
            course_id=course_id,
            priority_score=score,
            exam_days=exam_days,
            course_details=course_details,
        )

        # Estimate success probability
        from app.services.risk_analysis_service import risk_analysis_service
        success_prob = risk_analysis_service.estimate_success_probability(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )

        # Get risk level
        try:
            risk_resp = risk_analysis_service.calculate_risk_score(db, user_id, course_id)
            risk_level = risk_resp.risk_level
        except Exception:
            risk_level = RiskLevel.MEDIUM

        # Persist / upsert
        record = (
            db.query(PriorityScore)
            .filter(PriorityScore.user_id == user_id, PriorityScore.course_id == course_id)
            .first()
        )
        now = datetime.utcnow()
        if record:
            record.priority_score = score
            record.recommended_weekly_hours = recommended_hours
            record.success_probability = success_prob
            record.factors = factors
            record.calculated_at = now
        else:
            record = PriorityScore(
                user_id=user_id,
                course_id=course_id,
                priority_score=score,
                recommended_weekly_hours=recommended_hours,
                success_probability=success_prob,
                factors=factors,
                calculated_at=now,
            )
            db.add(record)
        db.commit()
        db.refresh(record)

        course_name = grade.course_name if grade else (
            course_details.get("name") if course_details else None
        )

        return PriorityScoreResponse(
            id=record.id,
            user_id=user_id,
            course_id=course_id,
            course_name=course_name,
            priority_score=score,
            recommended_weekly_hours=recommended_hours,
            success_probability=success_prob,
            risk_level=risk_level,
            factors=factors,
            calculated_at=record.calculated_at,
        )

    def calculate_all_priorities(
        self, db: Session, user_id: int
    ) -> List[PriorityScoreResponse]:
        """
        Calculate priority scores for all courses the student has grades for.
        Returns list sorted by priority_score descending.

        Requirements: 9.10
        """
        course_ids = (
            db.query(Grade.course_id)
            .filter(Grade.user_id == user_id)
            .distinct()
            .all()
        )
        course_ids = [row[0] for row in course_ids]

        results: List[PriorityScoreResponse] = []
        for cid in course_ids:
            try:
                score = self.calculate_priority_score(db, user_id, cid)
                results.append(score)
            except Exception as exc:
                logger.warning(
                    "[PriorityService] Failed for user=%d course=%d: %s",
                    user_id, cid, exc,
                )

        results.sort(key=lambda r: r.priority_score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Recommended study hours (Task 12.1)
    # ------------------------------------------------------------------

    def calculate_recommended_hours(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        priority_score: Optional[float] = None,
        exam_days: Optional[int] = None,
        course_details: Optional[Dict] = None,
    ) -> float:
        """
        Calculate recommended study hours per week for a course.

        Base = ECTS * 0.5 * difficulty_factor
        Increases by 50% when exam within 14 days.
        Clamped to [MIN_HOURS, MAX_HOURS].

        Requirements: 11.1–11.9
        """
        if course_details is None:
            course_details = self._get_course_details(db, course_id)

        ects = 1.0
        difficulty = 3  # default mid difficulty (1–5)

        if course_details:
            ects = course_details.get("ects_credits", 1.0) or 1.0
            difficulty = course_details.get("difficulty_level", 3) or 3

        # Base hours: ECTS × 0.5 × difficulty factor (scaled 1–5 → 0.5–1.5)
        difficulty_factor = 0.5 + (difficulty - 1) * 0.25  # maps 1→0.5, 3→1.0, 5→1.5
        base_hours = ects * 0.5 * difficulty_factor

        # Boost when exam is close (within 14 days)
        if exam_days is not None and exam_days <= 14:
            base_hours *= 1.5

        # Clamp to valid range
        hours = round(min(MAX_HOURS, max(MIN_HOURS, base_hours)), 2)

        logger.debug(
            "[PriorityService] Recommended hours user=%d course=%d: %.2f",
            user_id, course_id, hours,
        )
        return hours

    # ------------------------------------------------------------------
    # Priority formula internals
    # ------------------------------------------------------------------

    def _compute_priority(
        self,
        grade: Optional[Grade],
        course_details: Optional[Dict],
        exam_days: Optional[int],
        is_failed: bool,
        is_blocker: bool,
    ) -> Tuple[float, Dict]:
        """
        Apply the weighted priority formula and return (score, factors).

        Requirements: 9.2–9.9
        """
        factors: Dict = {}
        score = 0.0

        # --- ECTS Credits (30%) ---
        ects = 1.0
        max_ects = 30.0
        if course_details:
            ects = course_details.get("ects_credits", 1.0) or 1.0
        ects_contribution = (ects / max_ects) * 100 * W_ECTS
        score += ects_contribution
        factors["ects_contribution"] = round(ects_contribution, 2)

        # --- Coefficient (15%) ---
        coeff = 1.0
        max_coeff = 10.0
        if course_details:
            coeff = course_details.get("coefficient", 1.0) or 1.0
        coeff_contribution = (coeff / max_coeff) * 100 * W_COEFF
        score += coeff_contribution
        factors["coefficient_contribution"] = round(coeff_contribution, 2)

        # --- Exam Proximity (25%) ---
        exam_contribution = 0.0
        if exam_days is not None:
            if exam_days <= 7:
                exam_contribution = 25.0
            elif exam_days <= 30:
                exam_contribution = 25.0 - ((exam_days - 7) / 23.0) * 10.0
            elif exam_days <= 60:
                exam_contribution = 15.0 - ((exam_days - 30) / 30.0) * 10.0
            else:
                exam_contribution = 5.0
        score += exam_contribution
        factors["exam_proximity_contribution"] = round(exam_contribution, 2)
        factors["days_until_exam"] = exam_days

        # --- Current Grade (20%) ---
        grade_contribution = 0.0
        if grade and grade.grade_obtained is not None and grade.min_passing_grade:
            grade_ratio = grade.grade_obtained / grade.min_passing_grade
            # Invert: lower grade ratio → higher priority contribution
            inverted = max(0.0, 1.0 - min(grade_ratio, 1.0))
            grade_contribution = inverted * 100 * W_GRADE
        score += grade_contribution
        factors["grade_contribution"] = round(grade_contribution, 2)

        # --- Difficulty (10%) ---
        difficulty = 3
        if course_details:
            difficulty = course_details.get("difficulty_level", 3) or 3
        difficulty_contribution = (difficulty / 5.0) * 100 * W_DIFFICULTY
        score += difficulty_contribution
        factors["difficulty_contribution"] = round(difficulty_contribution, 2)

        # --- Bonuses ---
        bonus = 0.0
        if is_failed:
            bonus += BONUS_FAILED
            factors["bonus_failed"] = BONUS_FAILED
        if is_blocker:
            bonus += BONUS_BLOCKER
            factors["bonus_blocker"] = BONUS_BLOCKER
        score += bonus

        # --- Normalize to 0–100 ---
        final_score = round(min(100.0, max(0.0, score)), 2)
        factors["final_score"] = final_score
        return final_score, factors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_latest_grade(
        self, db: Session, user_id: int, course_id: int
    ) -> Optional[Grade]:
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.course_id == course_id)
            .order_by(Grade.attempt_number.desc())
            .first()
        )

    def _get_attempt_count(self, db: Session, user_id: int, course_id: int) -> int:
        return (
            db.query(Grade)
            .filter(Grade.user_id == user_id, Grade.course_id == course_id)
            .count()
        )

    def _get_course_details(self, db: Session, course_id: int) -> Optional[Dict]:
        try:
            import app.services.super_admin_client as client
            return client.fetch_course_details(db, course_id)
        except Exception:
            return None

    def _get_days_until_exam(
        self, db: Session, user_id: int, course_id: int
    ) -> Optional[int]:
        try:
            from app.services.exam_service import exam_service
            exam = exam_service.get_next_exam_for_course(db, user_id, course_id)
            return exam.days_until if exam else None
        except Exception:
            return None

    def _is_prerequisite_blocker(self, db: Session, course_id: int) -> bool:
        try:
            import app.services.super_admin_client as client
            prereq_map = client.fetch_prerequisite_map(db)
            for prereq_ids in prereq_map.values():
                if course_id in prereq_ids:
                    return True
            return False
        except Exception:
            return False


# Module-level singleton
priority_service = PriorityService()
