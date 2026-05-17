"""
Pydantic schemas for student profile
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ProfileBase(BaseModel):
    """Base schema for student profile"""
    cursus: str = Field(..., min_length=1, max_length=100, description="Academic program/cursus")
    academic_level: str = Field(..., min_length=1, max_length=50, description="Current academic level")
    weekly_study_goal: float = Field(..., ge=1.0, le=168.0, description="Weekly study goal in hours (1-168)")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences as JSON")


class ProfileCreate(ProfileBase):
    """Schema for creating a student profile"""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating a student profile"""
    cursus: Optional[str] = Field(None, min_length=1, max_length=100)
    academic_level: Optional[str] = Field(None, min_length=1, max_length=50)
    weekly_study_goal: Optional[float] = Field(None, ge=1.0, le=168.0)
    preferences: Optional[Dict[str, Any]] = None


class ProfileResponse(ProfileBase):
    """Schema for student profile response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
