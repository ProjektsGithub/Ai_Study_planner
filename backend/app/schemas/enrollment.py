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
    selected_td_slot_id: Optional[int] = Field(None, description="Selected TD (Übung) group slot ID")
    selected_tp_slot_id: Optional[int] = Field(None, description="Selected TP (Praktikum) group slot ID")


class EnrollmentResponse(BaseModel):
    """Enrollment record returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    priority_override: Optional[int]
    personal_notes: Optional[str]
    selected_td_slot_id: Optional[int] = None
    selected_tp_slot_id: Optional[int] = None
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


class ClassScheduleSlotBrief(BaseModel):
    """Class schedule slot attached to a course (Vorlesung/CM, Übung/TD, Praktikum/TP)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: Optional[int] = None
    course_name: str
    session_type: str  # CM, TD, TP, EXAM
    group_name: Optional[str] = None
    day_of_week: str
    start_time: str
    end_time: str
    room_location: Optional[str] = None
    is_fixed: bool = True
    is_mandatory: bool = True


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
    selected_td_slot_id: Optional[int] = None
    selected_tp_slot_id: Optional[int] = None

    # Available university schedule slots for this course (CM, TD groups, TP groups)
    schedule_slots: List[ClassScheduleSlotBrief] = []

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
