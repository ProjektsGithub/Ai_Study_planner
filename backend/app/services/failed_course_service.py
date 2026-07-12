"""
Failed Course Service
=====================

Tracks courses with validation_status='failed', identifies prerequisite
blockers, and calculates days since first failure.

Requirements: 4.1–4.7, 10.1–10.5, 10.7
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.grade import Grade
from app.schemas.analysis import (
    FailedCourseResponse,
    PrerequisiteBlockerResponse,
)
from app.schemas.grade import ValidationStatus
import app.services.super_admin_client as client

logger = logging.getLogger(__name__)


class FailedCourseService:
    """Identifies failed courses and prerequisite blockers."""

    def get_failed_courses(
        self, db: Session, user_id: int
    ) -> List[FailedCourseResponse]:
        """
        Retrieve all courses with validation_status='failed' for a student.
        Includes attempt count, days since first failure, and prerequisite
        blocker status.

        Requirements: 4.1, 4.2, 4.3, 4.6, 4.7
        """
        # Get all failed grades (could be multiple attempts per course)
        failed_grades = (
            db.query(Grade)
            .filter(
                Grade.user_id == user_id,
                Grade.validation_status == ValidationStatus.FAILED.value,
            )
            .order_by(Grade.course_id, Grade.attempt_number)
            .all()
        )

        # Group by course_id to get attempt count and earliest failure
        course_map: Dict[int, List[Grade]] = {}
        for g in failed_grades:
            course_map.setdefault(g.course_id, []).append(g)

        # Build prerequisite blocker info
        prerequisite_map = client.fetch_prerequisite_map(db)
        # Invert: which courses does each course_id block?
        blocked_by: Dict[int, List[int]] = {}
        for dependent_id, prereq_ids in prerequisite_map.items():
            for prereq_id in prereq_ids:
                blocked_by.setdefault(prereq_id, []).append(dependent_id)

        # Build set of all failed course_ids for quick lookup
        failed_course_ids = set(course_map.keys())

        result: List[FailedCourseResponse] = []
        for course_id, attempts in course_map.items():
            first_attempt = attempts[0]  # earliest (lowest attempt_number)
            latest_attempt = attempts[-1]  # most recent

            days_since = self.calculate_days_since_failure(
                first_attempt.created_at
            )

            # Is this failed course blocking any other course?
            blocked_courses = blocked_by.get(course_id, [])
            is_blocker = len(blocked_courses) > 0

            # Resolve blocked course names
            blocked_names: List[str] = []
            for blocked_id in blocked_courses:
                details = client.fetch_course_details(db, blocked_id)
                if details:
                    blocked_names.append(details["name"])

            result.append(
                FailedCourseResponse(
                    course_id=course_id,
                    course_name=first_attempt.course_name,
                    original_semester=first_attempt.semester,
                    attempt_count=len(attempts),
                    days_since_first_failure=days_since,
                    last_grade=latest_attempt.grade_obtained,
                    min_passing_grade=first_attempt.min_passing_grade,
                    ects_credits=first_attempt.ects_credits,
                    is_prerequisite_blocker=is_blocker,
                    blocks_courses=blocked_names,
                )
            )

        # Sort by days_since_first_failure descending (longest-failing first)
        result.sort(key=lambda x: x.days_since_first_failure, reverse=True)
        return result

    def identify_prerequisite_blockers(
        self, db: Session, user_id: int
    ) -> List[PrerequisiteBlockerResponse]:
        """
        Identify failed courses that are blocking other courses.

        Requirements: 4.6, 10.1, 10.2, 10.3, 10.4, 10.5, 10.7
        """
        failed_courses = self.get_failed_courses(db, user_id)
        blockers: List[PrerequisiteBlockerResponse] = []

        for fc in failed_courses:
            if not fc.is_prerequisite_blocker:
                continue

            # Resolve blocked course IDs from the prerequisite map
            prerequisite_map = client.fetch_prerequisite_map(db)
            blocked_by: Dict[int, List[int]] = {}
            for dep_id, prereq_ids in prerequisite_map.items():
                for p_id in prereq_ids:
                    blocked_by.setdefault(p_id, []).append(dep_id)

            blocked_ids = blocked_by.get(fc.course_id, [])
            blocked_names: List[str] = []
            for bid in blocked_ids:
                details = client.fetch_course_details(db, bid)
                if details:
                    blocked_names.append(details["name"])

            blockers.append(
                PrerequisiteBlockerResponse(
                    failed_course_id=fc.course_id,
                    failed_course_name=fc.course_name,
                    blocked_course_ids=blocked_ids,
                    blocked_course_names=blocked_names,
                    blocker_impact=len(blocked_ids),
                    days_since_first_failure=fc.days_since_first_failure,
                )
            )

        # Sort by blocker_impact descending (most blocking first)
        blockers.sort(key=lambda x: x.blocker_impact, reverse=True)
        return blockers

    def calculate_days_since_failure(
        self, first_failure_date: datetime
    ) -> int:
        """
        Calculate number of days since the first failed attempt.

        Args:
            first_failure_date: datetime of the first Grade record for this course.

        Requirements: 4.7
        """
        if isinstance(first_failure_date, datetime):
            first_date = first_failure_date.date()
        else:
            first_date = first_failure_date
        return (date.today() - first_date).days

    def get_failed_course_ids(self, db: Session, user_id: int) -> set:
        """Return set of course_ids that are currently failed (helper for other services)."""
        failed_grades = (
            db.query(Grade)
            .filter(
                Grade.user_id == user_id,
                Grade.validation_status == ValidationStatus.FAILED.value,
            )
            .all()
        )
        return {g.course_id for g in failed_grades}


# Module-level singleton
failed_course_service = FailedCourseService()
