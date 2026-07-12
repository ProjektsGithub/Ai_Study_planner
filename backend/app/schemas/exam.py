"""
Pydantic schemas for Exam management.

ExamType enum: midterm | final | practical | oral | project
weight: 0.0–1.0 (e.g. 0.4 = 40% of final grade)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum
import re


class ExamType(str, Enum):
    """Type of exam"""
    MIDTERM = "midterm"
    FINAL = "final"
    PRACTICAL = "practical"
    ORAL = "oral"
    PROJECT = "project"


class ExamBase(BaseModel):
    """Shared fields for exam create/update"""
    course_id: int = Field(..., description="Course ID from Super Admin Platform")
    course_name: str = Field(..., min_length=1, max_length=200, description="Course name")
    exam_date: date = Field(..., description="Exam date in YYYY-MM-DD format")
    exam_time: Optional[time] = Field(None, description="Exam time in HH:MM format")
    location: Optional[str] = Field(None, max_length=200, description="Exam room or location")
    exam_type: Optional[ExamType] = Field(None, description="Type of exam")
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Importance factor (0.0–1.0). E.g. 0.6 = 60% of final grade"
    )
    notes: Optional[str] = Field(None, description="Additional notes about the exam")

    @field_validator("exam_date", mode="before")
    @classmethod
    def validate_date_format(cls, v) -> date:
        """Accept date object or YYYY-MM-DD string"""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("Exam date must be in YYYY-MM-DD format")
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("Exam date must be in YYYY-MM-DD format")
        raise ValueError("Exam date must be in YYYY-MM-DD format")


class ExamCreate(ExamBase):
    """Schema for creating a new exam"""
    pass


class ExamUpdate(BaseModel):
    """Schema for updating an existing exam (all fields optional)"""
    exam_date: Optional[date] = Field(None, description="Exam date in YYYY-MM-DD format")
    exam_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=200)
    exam_type: Optional[ExamType] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None

    @field_validator("exam_date", mode="before")
    @classmethod
    def validate_date_format(cls, v) -> Optional[date]:
        """Accept date object or YYYY-MM-DD string"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("Exam date must be in YYYY-MM-DD format")
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("Exam date must be in YYYY-MM-DD format")
        raise ValueError("Exam date must be in YYYY-MM-DD format")


class ExamResponse(BaseModel):
    """Schema for exam response"""
    id: int
    user_id: int
    course_id: int
    course_name: str
    exam_date: date
    exam_time: Optional[time] = None
    location: Optional[str] = None
    exam_type: Optional[str] = None
    weight: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExamWithCountdown(ExamResponse):
    """Exam response enriched with days_until countdown"""
    days_until: int = Field(
        ...,
        description="Days until exam (negative if in the past)"
    )


class ExamListResponse(BaseModel):
    """Schema for list of exams"""
    exams: List[ExamWithCountdown]
    total: int
