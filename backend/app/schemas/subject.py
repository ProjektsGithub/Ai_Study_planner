"""
Pydantic schemas for Subject
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime


class SubjectBase(BaseModel):
    """Base schema for Subject"""
    name: str = Field(..., min_length=1, max_length=100, description="Subject name (1-100 characters)")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5 scale)")
    difficulty: int = Field(..., ge=1, le=5, description="Difficulty level (1-5 scale)")
    target_weekly_hours: float = Field(..., ge=0.5, le=168, description="Target weekly study hours (0.5-168 range)")
    exam_date: Optional[date] = Field(None, description="Exam date (must be future date)")
    
    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate that exam date is in the future"""
        if v is not None and v < date.today():
            raise ValueError("Exam date must be in the future")
        return v


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject"""
    pass


class SubjectUpdate(BaseModel):
    """Schema for updating a subject (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Subject name (1-100 characters)")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5 scale)")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty level (1-5 scale)")
    target_weekly_hours: Optional[float] = Field(None, ge=0.5, le=168, description="Target weekly study hours (0.5-168 range)")
    exam_date: Optional[date] = Field(None, description="Exam date (must be future date)")
    
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
