"""
Pydantic schemas for Subject
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


class SubjectBase(BaseModel):
    """Base schema for Subject"""
    name: str = Field(..., min_length=1, max_length=100, description="Subject name (1-100 characters)")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5 scale)")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5 scale)")
    target_weekly_hours: float = Field(..., ge=0.5, le=168, description="Target weekly study hours (0.5-168 range)")
    exam_date: Optional[date] = Field(None, description="Exam date")

    exam_type: Optional[str] = Field(None, pattern="^(written_exam|oral|project|continuous_assessment|mixed)$", description="Type of exam")
    ects_credits: Optional[float] = Field(None, ge=0, le=30, description="ECTS credits for this subject")
    coefficient: Optional[float] = Field(None, ge=0, le=10, description="Coefficient/weight in grade calculation")
    is_mandatory: bool = Field(True, description="Whether the subject is mandatory")
    validation_status: str = Field("in_progress", pattern="^(not_started|in_progress|validated|failed)$", description="Validation status")

    weekly_class_hours: Optional[float] = Field(None, ge=0, le=168, description="Total class hours per week")
    current_progress: float = Field(0.0, ge=0, le=100, description="Current progress percentage")
    weak_topics: Optional[List[str]] = Field(None, description="List of weak topics/chapters")
    # NOTE: no exam_date validator here — SubjectResponse (read) must not reject past dates


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject"""

    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v: Optional[date]) -> Optional[date]:
        """Only on creation: exam date must be in the future"""
        if v is not None and v < date.today():
            raise ValueError("Exam date must be in the future")
        return v


class SubjectUpdate(BaseModel):
    """Schema for updating a subject (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Subject name (1-100 characters)")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5 scale)")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty level (1-5 scale)")
    target_weekly_hours: Optional[float] = Field(None, ge=0.5, le=168, description="Target weekly study hours (0.5-168 range)")
    exam_date: Optional[date] = Field(None, description="Exam date (must be future date)")
    
    exam_type: Optional[str] = Field(None, pattern="^(written_exam|oral|project|continuous_assessment|mixed)$")
    ects_credits: Optional[float] = Field(None, ge=0, le=30)
    coefficient: Optional[float] = Field(None, ge=0, le=10)
    is_mandatory: Optional[bool] = None
    validation_status: Optional[str] = Field(None, pattern="^(not_started|in_progress|validated|failed)$")
    
    weekly_class_hours: Optional[float] = Field(None, ge=0, le=168)
    current_progress: Optional[float] = Field(None, ge=0, le=100)
    weak_topics: Optional[List[str]] = None
    
    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate that exam date is in the future"""
        if v is not None and v < date.today():
            raise ValueError("Exam date must be in the future")
        return v


class SubjectResponse(SubjectBase):
    """Schema for subject response"""
    id: int
    user_id: int
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class SubjectListResponse(BaseModel):
    """Schema for list of subjects"""
    subjects: list[SubjectResponse]
    total: int
