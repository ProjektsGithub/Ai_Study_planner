"""
Pydantic schemas for AI Context — the enriched JSON payload
sent to the Llama + LoRA study plan generation engine.

All timestamps are ISO 8601. All floats are 2 decimal precision.
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time


# ---------------------------------------------------------------------------
# Sub-schemas matching the AI context JSON structure (design.md §8)
# ---------------------------------------------------------------------------

class AIStudentProfile(BaseModel):
    """Student profile section of AI context"""
    university_id: Optional[int] = None
    university_name: Optional[str] = None
    filiere_id: Optional[int] = None
    filiere_name: Optional[str] = None
    cursus_id: Optional[int] = None
    cursus_name: Optional[str] = None
    current_semester: Optional[int] = None
    academic_year: Optional[int] = None


class AIAcademicProgress(BaseModel):
    """ECTS progression section of AI context"""
    ects_obtained: float
    ects_required: float
    ects_remaining: float
    progression_percentage: float

    @field_serializer("ects_obtained", "ects_required", "ects_remaining", "progression_percentage")
    def serialize_float(self, v: float) -> float:
        return round(v, 2)


class AIFailedCourse(BaseModel):
    """Single failed course entry in AI context"""
    course_id: int
    course_name: str
    original_semester: Optional[int] = None
    attempt_count: int
    days_since_first_failure: int
    is_prerequisite_blocker: bool = False
    blocks_courses: List[str] = []


class AICoursePriority(BaseModel):
    """Priority/analysis entry per course in AI context"""
    course_id: int
    course_name: str
    priority_score: float
    risk_level: str  # low | medium | high
    recommended_weekly_hours: Optional[float] = None
    success_probability: Optional[float] = None

    @field_serializer("priority_score")
    def serialize_score(self, v: float) -> float:
        return round(v, 2)

    @field_serializer("recommended_weekly_hours", "success_probability")
    def serialize_opt_float(self, v: Optional[float]) -> Optional[float]:
        return round(v, 2) if v is not None else None


class AIAvailabilitySlot(BaseModel):
    """Availability slot entry in AI context"""
    day: str           # e.g. "Monday"
    start_time: str    # HH:MM:SS
    end_time: str
    energy_level: Optional[str] = None  # high | medium | low


class AIConstraint(BaseModel):
    """Constraint entry in AI context"""
    type: str          # student_job | internship | extracurricular | other
    schedule: Optional[str] = None
    active: bool = True


class AIUpcomingExam(BaseModel):
    """Upcoming exam entry in AI context"""
    course_id: int
    course_name: str
    exam_date: str     # ISO 8601 date string: YYYY-MM-DD
    exam_time: Optional[str] = None  # HH:MM:SS
    location: Optional[str] = None
    exam_type: Optional[str] = None
    weight: float
    days_until: int

    @field_serializer("weight")
    def serialize_weight(self, v: float) -> float:
        return round(v, 2)


# ---------------------------------------------------------------------------
# Top-level AI context
# ---------------------------------------------------------------------------

class AIContextResponse(BaseModel):
    """
    Complete AI context JSON sent to Llama + LoRA.
    Matches the structure defined in design.md §8.
    """
    student_profile: AIStudentProfile
    academic_progress: AIAcademicProgress
    failed_courses: List[AIFailedCourse] = []
    course_priorities: List[AICoursePriority] = []
    availability_slots: List[AIAvailabilitySlot] = []
    constraints: List[AIConstraint] = []
    upcoming_exams: List[AIUpcomingExam] = []
    generated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of context generation"
    )


class AIContextRequest(BaseModel):
    """Optional request body for AI context endpoint (reserved for future filters)"""
    include_risk_details: bool = Field(
        default=True,
        description="Include detailed risk factor breakdown"
    )
    include_priority_factors: bool = Field(
        default=True,
        description="Include detailed priority factor breakdown"
    )
