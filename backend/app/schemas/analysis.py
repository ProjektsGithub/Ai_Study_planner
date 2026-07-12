"""
Pydantic schemas for academic analysis results:
  - RiskScore       : risk level per course (low | medium | high)
  - PriorityScore   : priority score 0–100 per course
  - FailedCourse    : failed course details with days_since_first_failure
  - PrerequisiteBlocker: failed prerequisite blocking other courses
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Academic risk level for a course"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Risk Score
# ---------------------------------------------------------------------------

class RiskScoreResponse(BaseModel):
    """Risk score for a single course"""
    id: Optional[int] = None
    user_id: int
    course_id: int
    course_name: Optional[str] = None
    risk_level: RiskLevel
    factors: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON breakdown of contributing risk factors"
    )
    calculated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RiskScoreListResponse(BaseModel):
    """List of risk scores for all enrolled courses"""
    risk_scores: List[RiskScoreResponse]
    total: int


# ---------------------------------------------------------------------------
# Priority Score
# ---------------------------------------------------------------------------

class PriorityScoreResponse(BaseModel):
    """Priority score for a single course"""
    id: Optional[int] = None
    user_id: int
    course_id: int
    course_name: Optional[str] = None
    priority_score: float = Field(..., description="Priority score 0–100")
    recommended_weekly_hours: Optional[float] = Field(
        None,
        description="Recommended study hours per week"
    )
    success_probability: Optional[float] = Field(
        None,
        description="Estimated probability of passing (0–100%)"
    )
    risk_level: Optional[RiskLevel] = None
    factors: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON breakdown of the weighted priority calculation"
    )
    calculated_at: Optional[datetime] = None

    @field_serializer("priority_score")
    def serialize_priority_score(self, v: float) -> float:
        return round(v, 2)

    @field_serializer("recommended_weekly_hours")
    def serialize_hours(self, v: Optional[float]) -> Optional[float]:
        return round(v, 2) if v is not None else None

    @field_serializer("success_probability")
    def serialize_probability(self, v: Optional[float]) -> Optional[float]:
        return round(v, 2) if v is not None else None

    model_config = {"from_attributes": True}


class PriorityScoreListResponse(BaseModel):
    """Priority scores sorted descending by priority_score"""
    priorities: List[PriorityScoreResponse]
    total: int


# ---------------------------------------------------------------------------
# Failed Course
# ---------------------------------------------------------------------------

class FailedCourseResponse(BaseModel):
    """A course with validation_status='failed'"""
    course_id: int
    course_name: str
    original_semester: Optional[int] = Field(
        None,
        description="Semester when the course was first attempted"
    )
    attempt_count: int = Field(..., description="Total number of attempts")
    days_since_first_failure: int = Field(
        ...,
        description="Days elapsed since the first failed attempt"
    )
    last_grade: Optional[float] = None
    min_passing_grade: Optional[float] = None
    ects_credits: Optional[float] = None
    is_prerequisite_blocker: bool = Field(
        default=False,
        description="True if this failed course blocks other courses"
    )
    blocks_courses: List[str] = Field(
        default_factory=list,
        description="Names of courses blocked by this failed prerequisite"
    )


class FailedCourseListResponse(BaseModel):
    """List of all failed courses for a student"""
    failed_courses: List[FailedCourseResponse]
    total: int


# ---------------------------------------------------------------------------
# Prerequisite Blocker
# ---------------------------------------------------------------------------

class PrerequisiteBlockerResponse(BaseModel):
    """A failed course that is blocking progression to other courses"""
    failed_course_id: int
    failed_course_name: str
    blocked_course_ids: List[int] = []
    blocked_course_names: List[str] = []
    blocker_impact: int = Field(
        ...,
        description="Number of courses blocked by this failed prerequisite"
    )
    days_since_first_failure: int
