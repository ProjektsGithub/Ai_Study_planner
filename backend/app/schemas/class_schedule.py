"""
Pydantic schemas for ClassSchedule (University Timetable)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import time, datetime


class ClassScheduleBase(BaseModel):
    study_program_id: int
    academic_track_id: Optional[int] = None
    semester_id: Optional[int] = None
    course_id: Optional[int] = None
    course_name: str = Field(..., max_length=255)
    course_code: Optional[str] = Field(None, max_length=50)
    day_of_week: str = Field(..., pattern="^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$")
    start_time: time
    end_time: time
    session_type: str = Field("CM", description="CM (Lecture), TD (Tutorial), TP (Lab), EXAM")
    room_location: Optional[str] = Field(None, max_length=100)
    is_mandatory: bool = True


class ClassScheduleCreate(ClassScheduleBase):
    pass


class ClassScheduleUpdate(BaseModel):
    study_program_id: Optional[int] = None
    academic_track_id: Optional[int] = None
    semester_id: Optional[int] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    session_type: Optional[str] = None
    room_location: Optional[str] = None
    is_mandatory: Optional[bool] = None


class ClassScheduleResponse(ClassScheduleBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassScheduleListResponse(BaseModel):
    items: List[ClassScheduleResponse]
    total: int
