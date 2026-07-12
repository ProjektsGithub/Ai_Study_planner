"""
Pydantic schemas for Grade management.

ValidationStatus enum:
    - in_progress: no grade entered yet
    - validated:   grade_obtained >= min_passing_grade
    - failed:      grade_obtained < min_passing_grade
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status for a course grade"""
    VALIDATED = "validated"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class GradeBase(BaseModel):
    """Shared fields for grade create/update"""
    course_id: int = Field(..., description="Course ID from Super Admin Platform")
    course_name: str = Field(..., min_length=1, max_length=200, description="Course name")
    grade_obtained: Optional[float] = Field(
        None,
        description="Grade obtained (None means in_progress)"
    )
    min_passing_grade: float = Field(
        ...,
        gt=0,
        description="Minimum passing grade (must be positive)"
    )
    max_grade: float = Field(
        default=20.0,
        gt=0,
        description="Maximum possible grade (default 20.0)"
    )
    attempt_number: int = Field(
        default=1,
        ge=1,
        description="Attempt number (incremented on retake)"
    )
    semester: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Semester when this grade was obtained"
    )
    ects_credits: Optional[float] = Field(
        None,
        ge=0,
        description="ECTS credits for this course"
    )
    coefficient: Optional[float] = Field(
        None,
        ge=0,
        description="Course coefficient for grade calculations"
    )

    @field_validator("grade_obtained")
    @classmethod
    def validate_grade_range(cls, v: Optional[float]) -> Optional[float]:
        """grade_obtained is validated against max_grade in model_validator below"""
        return v

    @model_validator(mode="after")
    def validate_grade_within_range(self) -> "GradeBase":
        """Grade must be between 0 and max_grade"""
        if self.grade_obtained is not None:
            if self.grade_obtained < 0:
                raise ValueError("Grade must be between 0 and maximum grade for this course")
            if self.grade_obtained > self.max_grade:
                raise ValueError(
                    f"Grade must be between 0 and maximum grade for this course "
                    f"(max: {self.max_grade})"
                )
        return self


class GradeCreate(GradeBase):
    """Schema for creating a new grade entry"""
    pass


class GradeUpdate(BaseModel):
    """Schema for updating an existing grade (all fields optional)"""
    grade_obtained: Optional[float] = Field(None, description="Updated grade value")
    min_passing_grade: Optional[float] = Field(None, gt=0)
    max_grade: Optional[float] = Field(None, gt=0)
    attempt_number: Optional[int] = Field(None, ge=1)
    semester: Optional[int] = Field(None, ge=1, le=20)
    ects_credits: Optional[float] = Field(None, ge=0)
    coefficient: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_grade_within_range(self) -> "GradeUpdate":
        """Grade must be between 0 and max_grade if both provided"""
        if self.grade_obtained is not None:
            if self.grade_obtained < 0:
                raise ValueError("Grade must be between 0 and maximum grade for this course")
            if self.max_grade is not None and self.grade_obtained > self.max_grade:
                raise ValueError(
                    f"Grade must be between 0 and maximum grade for this course "
                    f"(max: {self.max_grade})"
                )
        return self


class GradeResponse(BaseModel):
    """Schema for grade response with auto-calculated validation_status"""
    id: int
    user_id: int
    course_id: int
    course_name: str
    grade_obtained: Optional[float] = None
    min_passing_grade: float
    max_grade: float
    validation_status: ValidationStatus
    attempt_number: int
    semester: Optional[int] = None
    ects_credits: Optional[float] = None
    coefficient: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GradeListResponse(BaseModel):
    """Schema for list of grades"""
    grades: List[GradeResponse]
    total: int
