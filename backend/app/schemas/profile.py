"""
Pydantic schemas for student profile
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, date


class ProfileBase(BaseModel):
    """Base schema for student profile"""
    cursus: Optional[str] = Field(default="Général", max_length=100, description="Academic program/cursus")
    academic_level: str = Field(..., min_length=1, max_length=50, description="Current academic level")
    weekly_study_goal: float = Field(..., ge=1.0, le=168.0, description="Weekly study goal in hours (1-168)")
    
    semester_start_date: Optional[date] = Field(default=None, description="Start date of current semester")
    semester_end_date: Optional[date] = Field(default=None, description="End date of current semester")
    exam_period_start: Optional[date] = Field(default=None, description="Start date of exam period")
    
    total_course_hours_per_week: Optional[float] = Field(default=None, ge=0, le=168, description="Total class hours per week")
    other_commitments_hours: Optional[float] = Field(default=None, ge=0, le=168, description="Other commitments hours per week")
    
    preferred_study_time: Optional[str] = Field(default=None, pattern="^(morning|afternoon|evening|night|flexible)$", description="Preferred study time")
    preferred_session_duration: Optional[int] = Field(default=None, ge=15, le=240, description="Preferred session duration in minutes")
    study_pace: Optional[str] = Field(default=None, pattern="^(intensive|balanced|moderate|relaxed)$", description="Study pace preference")
    
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Additional user preferences as JSON")

    @field_validator("cursus", mode="before")
    @classmethod
    def set_default_cursus(cls, v: Any) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "Général"
        return str(v).strip()

    @field_validator("study_pace", mode="before")
    @classmethod
    def normalize_study_pace(cls, v: Any) -> Optional[str]:
        if not v:
            return None
        if isinstance(v, str) and v.strip() == "moderate":
            return "balanced"
        return v


class ProfileCreate(ProfileBase):
    """Schema for creating a student profile"""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating a student profile"""
    cursus: Optional[str] = Field(None, max_length=100)
    academic_level: Optional[str] = Field(None, min_length=1, max_length=50)
    weekly_study_goal: Optional[float] = Field(None, ge=1.0, le=168.0)
    
    semester_start_date: Optional[date] = None
    semester_end_date: Optional[date] = None
    exam_period_start: Optional[date] = None
    
    total_course_hours_per_week: Optional[float] = Field(None, ge=0, le=168)
    other_commitments_hours: Optional[float] = Field(None, ge=0, le=168)
    
    preferred_study_time: Optional[str] = Field(None, pattern="^(morning|afternoon|evening|night|flexible)$")
    preferred_session_duration: Optional[int] = Field(None, ge=15, le=240)
    study_pace: Optional[str] = Field(None, pattern="^(intensive|balanced|moderate|relaxed)$")
    
    preferences: Optional[Dict[str, Any]] = None

    @field_validator("cursus", mode="before")
    @classmethod
    def set_default_cursus_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return "Général"
        return str(v).strip()

    @field_validator("study_pace", mode="before")
    @classmethod
    def normalize_study_pace_update(cls, v: Any) -> Optional[str]:
        if not v:
            return None
        if isinstance(v, str) and v.strip() == "moderate":
            return "balanced"
        return v


class ProfileResponse(ProfileBase):
    """Schema for student profile response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
