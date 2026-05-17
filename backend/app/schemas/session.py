"""
Pydantic schemas for study session editing
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import time


class SessionCreateRequest(BaseModel):
    """Request schema for creating a new session"""
    subject_id: int = Field(..., description="Subject ID")
    day: str = Field(..., description="Day of week (Monday-Sunday)")
    start_time: str = Field(..., description="Start time in HH:MM:SS format")
    end_time: str = Field(..., description="End time in HH:MM:SS format")
    task_type: str = Field(..., description="Task type (lecture_review, exercise_practice, exam_preparation, project_work, reading)")
    notes: Optional[str] = Field("", description="Optional notes")
    
    @field_validator("day")
    @classmethod
    def validate_day(cls, v: str) -> str:
        """Validate day of week"""
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if v not in valid_days:
            raise ValueError(f"day must be one of {valid_days}")
        return v
    
    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        """Validate task type"""
        valid_types = ["lecture_review", "exercise_practice", "exam_preparation", "project_work", "reading"]
        if v not in valid_types:
            raise ValueError(f"task_type must be one of {valid_types}")
        return v
    
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format HH:MM:SS"""
        try:
            # Try to parse as time
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM:SS format")
    
    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v: str, info) -> str:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data:
            start = time.fromisoformat(info.data['start_time'])
            end = time.fromisoformat(v)
            if end <= start:
                raise ValueError("end_time must be after start_time")
        return v


class SessionUpdateRequest(BaseModel):
    """Request schema for updating an existing session"""
    subject_id: Optional[int] = Field(None, description="Subject ID")
    day: Optional[str] = Field(None, description="Day of week (Monday-Sunday)")
    start_time: Optional[str] = Field(None, description="Start time in HH:MM:SS format")
    end_time: Optional[str] = Field(None, description="End time in HH:MM:SS format")
    task_type: Optional[str] = Field(None, description="Task type")
    notes: Optional[str] = Field(None, description="Optional notes")
    
    @field_validator("day")
    @classmethod
    def validate_day(cls, v: Optional[str]) -> Optional[str]:
        """Validate day of week"""
        if v is None:
            return v
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if v not in valid_days:
            raise ValueError(f"day must be one of {valid_days}")
        return v
    
    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate task type"""
        if v is None:
            return v
        valid_types = ["lecture_review", "exercise_practice", "exam_preparation", "project_work", "reading"]
        if v not in valid_types:
            raise ValueError(f"task_type must be one of {valid_types}")
        return v
    
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format HH:MM:SS"""
        if v is None:
            return v
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM:SS format")


class SessionResponse(BaseModel):
    """Response schema for a session"""
    id: int
    study_plan_id: int
    subject_id: int
    subject_name: str
    day: str
    start_time: str
    end_time: str
    task_type: str
    notes: str
    
    class Config:
        from_attributes = True
