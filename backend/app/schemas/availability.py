"""
Pydantic schemas for Availability
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import time, datetime
from enum import Enum


class DayOfWeek(str, Enum):
    """Enum for days of the week"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class EnergyLevel(str, Enum):
    """Enum for energy levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AvailabilityBase(BaseModel):
    """Base schema for Availability"""
    day_of_week: DayOfWeek = Field(..., description="Day of the week (Monday-Sunday)")
    start_time: time = Field(..., description="Start time in HH:MM format (24-hour)")
    end_time: time = Field(..., description="End time in HH:MM format (24-hour)")
    energy_level: Optional[EnergyLevel] = Field(None, description="Energy level during this time slot")
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v: time, info) -> time:
        """Validate that end_time is after start_time"""
        if 'start_time' in info.data:
            start_time = info.data['start_time']
            if v <= start_time:
                raise ValueError("End time must be after start time")
        return v


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating a new availability"""
    pass


class AvailabilityUpdate(BaseModel):
    """Schema for updating an availability (all fields optional)"""
    day_of_week: Optional[DayOfWeek] = Field(None, description="Day of the week (Monday-Sunday)")
    start_time: Optional[time] = Field(None, description="Start time in HH:MM format (24-hour)")
    end_time: Optional[time] = Field(None, description="End time in HH:MM format (24-hour)")
    energy_level: Optional[EnergyLevel] = Field(None, description="Energy level during this time slot")
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v: Optional[time], info) -> Optional[time]:
        """Validate that end_time is after start_time"""
        if v is not None and 'start_time' in info.data and info.data['start_time'] is not None:
            start_time = info.data['start_time']
            if v <= start_time:
                raise ValueError("End time must be after start time")
        return v


class AvailabilityResponse(BaseModel):
    """Schema for availability response"""
    id: int
    user_id: int
    day_of_week: str
    start_time: time
    end_time: time
    energy_level: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class AvailabilityListResponse(BaseModel):
    """Schema for list of availabilities"""
    availabilities: list[AvailabilityResponse]
    total: int
