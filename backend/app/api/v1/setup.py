"""
Setup Status Endpoint
Returns a simple object indicating which onboarding steps the student has completed.
Used by the dashboard to show/hide the SetupProgressBanner.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.study_plan import StudyPlan

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("/status")
async def get_setup_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the onboarding completion status for the authenticated student.

    Steps:
      1. has_profile      — StudentProfile exists with cursus_id set
      2. has_courses      — at least one Subject exists (populated via enrollment sync)
      3. has_availabilities — at least one Availability slot defined
      4. has_plan         — at least one StudyPlan with status='generated'
    """
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    has_profile = bool(
        profile and profile.cursus_id and profile.current_semester
    )

    has_courses = db.query(Subject).filter(
        Subject.user_id == current_user.id
    ).count() > 0

    has_availabilities = db.query(Availability).filter(
        Availability.user_id == current_user.id
    ).count() > 0

    has_plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == current_user.id,
        StudyPlan.status == "generated",
    ).count() > 0

    completed = sum([has_profile, has_courses, has_availabilities, has_plan])

    return {
        "has_profile": has_profile,
        "has_courses": has_courses,
        "has_availabilities": has_availabilities,
        "has_plan": has_plan,
        "completed_steps": completed,
        "is_complete": completed == 4,
    }
