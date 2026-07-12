"""
Enrollment-to-Subject Synchronization Service

When a student qualifies a course from the admin catalogue, this service
mirrors the data into the legacy `subjects` table so the AI planning
engine can use it without modifications.

Sync rules:
  - status=in_progress  → create/update Subject (normal priority)
  - status=retake       → create/update Subject (high priority=5, URGENT)
  - status=optional     → create/update Subject (low priority=1)
  - status=validated    → delete Subject (remove from AI planning)
  - enrollment removed  → delete Subject
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.student_course_enrollment import StudentCourseEnrollment
from app.models.course import Course

# Mapping from enrollment status → subject priority (1-5)
STATUS_TO_PRIORITY = {
    "retake": 5,       # Highest — must pass
    "in_progress": 3,  # Normal
    "optional": 1,     # Low — schedule only if time allows
}

# How many hours per week to suggest based on ECTS credits
# Rule of thumb: 1 ECTS ≈ 25-30h workload over a semester (~18 weeks)
# → ~1.5h/week per ECTS credit
ECTS_TO_WEEKLY_HOURS = 1.5
DEFAULT_WEEKLY_HOURS = 2.0


def _compute_weekly_hours(course: Course) -> float:
    """Estimate recommended weekly study hours from ECTS credits."""
    if course.ects_credits and course.ects_credits > 0:
        return round(min(course.ects_credits * ECTS_TO_WEEKLY_HOURS, 20.0), 1)
    return DEFAULT_WEEKLY_HOURS


def _get_validation_status(enrollment_status: str) -> str:
    """Map enrollment status to legacy Subject.validation_status values."""
    return {
        "in_progress": "in_progress",
        "retake": "failed",
        "optional": "in_progress",
        "validated": "validated",
    }.get(enrollment_status, "in_progress")


def sync_enrollment_to_subject(
    db: Session,
    enrollment: StudentCourseEnrollment,
    course: Course,
) -> Optional[Subject]:
    """
    Create or update a Subject record to mirror an enrollment.

    Returns the Subject if created/updated, None if the course is
    'validated' (removed from AI planning).
    """
    user_id = enrollment.user_id

    # Find existing Subject linked to this catalog course
    existing = db.query(Subject).filter(
        Subject.user_id == user_id,
        Subject.catalog_course_id == course.id,
    ).first()

    # If validated → remove from planning entirely
    if enrollment.status == "validated":
        if existing:
            db.delete(existing)
            db.commit()
        return None

    priority = STATUS_TO_PRIORITY.get(enrollment.status, 3)
    weekly_hours = _compute_weekly_hours(course)
    validation_status = _get_validation_status(enrollment.status)

    if existing:
        # Update all fields derived from the catalogue + enrollment
        existing.name = course.name
        existing.priority = priority
        existing.difficulty = course.difficulty_level
        existing.target_weekly_hours = weekly_hours
        existing.ects_credits = float(course.ects_credits) if course.ects_credits else None
        existing.coefficient = float(course.coefficient) if course.coefficient else None
        existing.is_mandatory = enrollment.status == "retake"
        existing.validation_status = validation_status
        db.commit()
        db.refresh(existing)
        return existing

    # Create new Subject
    subject = Subject(
        user_id=user_id,
        name=course.name,
        priority=priority,
        difficulty=course.difficulty_level,
        target_weekly_hours=weekly_hours,
        ects_credits=float(course.ects_credits) if course.ects_credits else None,
        coefficient=float(course.coefficient) if course.coefficient else None,
        is_mandatory=enrollment.status == "retake",
        validation_status=validation_status,
        catalog_course_id=course.id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def remove_subject_for_enrollment(
    db: Session,
    user_id: int,
    course_id: int,
) -> None:
    """Remove the Subject linked to a catalog course when enrollment is deleted."""
    existing = db.query(Subject).filter(
        Subject.user_id == user_id,
        Subject.catalog_course_id == course_id,
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
