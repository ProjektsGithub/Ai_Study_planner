"""
Pydantic schemas for student course enrollment
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Enrollment schemas
# ---------------------------------------------------------------------------

VALID_STATUSES = ["in_progress", "validated", "retake", "optional"]


class EnrollmentUpsert(BaseModel):
    """Create or update an enrollment for a single course."""
    course_id: int = Field(..., description="ID of the catalog course")
    status: str = Field(
        "in_progress",
        pattern="^(in_progress|validated|retake|optional)$",
        description="Student qualification status for this course",
    )
    priority_override: Optional[int] = Field(None, ge=1, le=5, description="Override AI priority (1=low, 5=critical)")
    personal_notes: Optional[str] = Field(None, max_length=1000, description="Student personal notes")


class EnrollmentResponse(BaseModel):
    """Enrollment record returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    priority_override: Optional[int]
    personal_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Schemas for the catalog view (courses from the admin platform)
# ---------------------------------------------------------------------------

class TeachingUnitBrief(BaseModel):
    """Lightweight teaching unit info embedded in course responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: Optional[str]
    ects_required: Optional[int]


class CatalogCourseResponse(BaseModel):
    """A catalog course enriched with the student's enrollment status."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: Optional[str]
    description: Optional[str]
    ects_credits: int
    coefficient: float
    difficulty_level: int
    teaching_unit_id: Optional[int]
    teaching_unit: Optional[TeachingUnitBrief]

    # Enrollment info (None if not yet enrolled)
    enrollment_id: Optional[int] = None
    enrollment_status: Optional[str] = None
    priority_override: Optional[int] = None
    personal_notes: Optional[str] = None

    # Retake info (German Wiederholung system)
    is_retake: bool = False  # True if this course belongs to a retake semester
    retake_semester_number: Optional[int] = None  # Which semester number is being retaken


class SemesterCoursesResponse(BaseModel):
    """All courses for the student's current semester + retake semesters, grouped by teaching unit."""
    semester_id: int
    semester_name: str
    semester_number: int
    cursus_name: str
    total_courses: int
    enrolled_courses: int
    courses: List[CatalogCourseResponse]
    retake_semesters: List[int] = []  # Semester numbers being retaken
