"""
Pydantic schemas for study plan generation and retrieval
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date, time


class GeneratePlanRequest(BaseModel):
    """Request schema for plan generation"""
    week_start: date = Field(..., description="Start date of the week (should be Monday)")
    force_regenerate: bool = Field(False, description="Force regeneration even if cached plan exists")
    
    @field_validator("week_start")
    @classmethod
    def validate_week_start(cls, v: date) -> date:
        """Validate that week_start is a Monday"""
        if v.weekday() != 0:  # 0 = Monday
            raise ValueError("week_start must be a Monday")
        return v


class StudySessionResponse(BaseModel):
    """Response schema for a study session"""
    id: int
    subject_id: int
    subject_name: str
    day: str
    start_time: str
    end_time: str
    task_type: str
    notes: str
    
    class Config:
        from_attributes = True


class StudyPlanResponse(BaseModel):
    """Response schema for a study plan"""
    plan_id: str
    week_start: str
    status: str
    summary: str
    edited: bool
    created_at: str
    sessions: List[StudySessionResponse]
    total_hours: float
    
    class Config:
        from_attributes = True


class GeneratePlanResponse(BaseModel):
    """Response schema for plan generation"""
    success: bool
    plan_id: Optional[str] = None
    plan: Optional[dict] = None
    corrections_made: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    from_cache: Optional[bool] = None
    generation_time: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None


class StudyPlanHistoryItem(BaseModel):
    """Single plan item in history list"""
    plan_id: str
    week_start: str
    status: str
    edited: bool
    created_at: str
    session_count: int
    total_hours: float
    
    class Config:
        from_attributes = True


class StudyPlanHistoryResponse(BaseModel):
    """Response schema for plan history with pagination"""
    plans: List[StudyPlanHistoryItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True
