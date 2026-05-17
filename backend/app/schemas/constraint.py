"""
Pydantic schemas for Constraint
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import time, datetime
from enum import Enum


class ConstraintType(str, Enum):
    """Enum for constraint types"""
    FORBIDDEN_SLOT = "forbidden_slot"
    MAX_DAILY_HOURS = "max_daily_hours"
    REQUIRED_BREAK = "required_break"
    FIXED_SLOT = "fixed_slot"


class DayOfWeek(str, Enum):
    """Enum for days of the week"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class ConstraintBase(BaseModel):
    """Base schema for Constraint"""
    constraint_type: ConstraintType = Field(..., description="Type of constraint")
    parameters: Dict[str, Any] = Field(..., description="Type-specific parameters")
    active: bool = Field(True, description="Whether constraint is active")
    
    @model_validator(mode='after')
    def validate_parameters(self):
        """Validate parameters based on constraint type"""
        constraint_type = self.constraint_type
        params = self.parameters
        
        if constraint_type == ConstraintType.FORBIDDEN_SLOT:
            # Required: day_of_week, start_time, end_time
            required_fields = ["day_of_week", "start_time", "end_time"]
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"forbidden_slot requires '{field}' in parameters")
            
            # Validate day_of_week
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if params["day_of_week"] not in valid_days:
                raise ValueError(f"day_of_week must be one of {valid_days}")
            
            # Validate time format and range
            try:
                start = datetime.strptime(params["start_time"], "%H:%M:%S").time()
                end = datetime.strptime(params["end_time"], "%H:%M:%S").time()
                if end <= start:
                    raise ValueError("end_time must be after start_time")
            except (ValueError, KeyError) as e:
                raise ValueError(f"Invalid time format in forbidden_slot: {e}")
        
        elif constraint_type == ConstraintType.MAX_DAILY_HOURS:
            # Required: max_hours
            if "max_hours" not in params:
                raise ValueError("max_daily_hours requires 'max_hours' in parameters")
            
            max_hours = params["max_hours"]
            if not isinstance(max_hours, (int, float)) or max_hours < 1 or max_hours > 24:
                raise ValueError("max_hours must be between 1 and 24")
        
        elif constraint_type == ConstraintType.REQUIRED_BREAK:
            # Required: duration_minutes, after_minutes
            required_fields = ["duration_minutes", "after_minutes"]
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"required_break requires '{field}' in parameters")
            
            duration = params["duration_minutes"]
            after = params["after_minutes"]
            
            if not isinstance(duration, int) or duration < 5 or duration > 120:
                raise ValueError("duration_minutes must be between 5 and 120")
            
            if not isinstance(after, int) or after < 30 or after > 240:
                raise ValueError("after_minutes must be between 30 and 240")
        
        elif constraint_type == ConstraintType.FIXED_SLOT:
            # Required: day_of_week, start_time, end_time, subject_id
            required_fields = ["day_of_week", "start_time", "end_time", "subject_id"]
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"fixed_slot requires '{field}' in parameters")
            
            # Validate day_of_week
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if params["day_of_week"] not in valid_days:
                raise ValueError(f"day_of_week must be one of {valid_days}")
            
            # Validate time format and range
            try:
                start = datetime.strptime(params["start_time"], "%H:%M:%S").time()
                end = datetime.strptime(params["end_time"], "%H:%M:%S").time()
                if end <= start:
                    raise ValueError("end_time must be after start_time")
            except (ValueError, KeyError) as e:
                raise ValueError(f"Invalid time format in fixed_slot: {e}")
            
            # Validate subject_id
            if not isinstance(params["subject_id"], int) or params["subject_id"] <= 0:
                raise ValueError("subject_id must be a positive integer")
        
        return self


class ConstraintCreate(ConstraintBase):
    """Schema for creating a new constraint"""
    pass


class ConstraintUpdate(BaseModel):
    """Schema for updating a constraint"""
    constraint_type: Optional[ConstraintType] = Field(None, description="Type of constraint")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Type-specific parameters")
    active: Optional[bool] = Field(None, description="Whether constraint is active")
    
    @model_validator(mode='after')
    def validate_parameters(self):
        """Validate parameters based on constraint type if both are provided"""
        if self.constraint_type is not None and self.parameters is not None:
            # Create a temporary ConstraintBase to validate
            temp = ConstraintBase(
                constraint_type=self.constraint_type,
                parameters=self.parameters,
                active=self.active if self.active is not None else True
            )
        return self


class ConstraintResponse(BaseModel):
    """Schema for constraint response"""
    id: int
    user_id: int
    constraint_type: str
    parameters: Dict[str, Any]
    active: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class ConstraintListResponse(BaseModel):
    """Schema for list of constraints"""
    constraints: list[ConstraintResponse]
    total: int
    active_count: int
    inactive_count: int
