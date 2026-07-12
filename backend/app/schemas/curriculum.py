"""
Pydantic schemas for Curriculum entities (Course, Semester, TeachingUnit, AcademicTrack)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class TrackLevel(str, Enum):
    """Enum for academic track levels"""
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"


# ==================== Academic Track Schemas ====================

class AcademicTrackBase(BaseModel):
    """Base schema for AcademicTrack"""
    study_program_id: int = Field(..., description="ID of the study program this track belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Track name (1-255 characters)")
    name_de: Optional[str] = Field(None, max_length=255, description="German track name")
    level: TrackLevel = Field(..., description="Academic level (bachelor, master, doctorate)")
    description: Optional[str] = Field(None, description="Track description")
    description_de: Optional[str] = Field(None, description="German track description")
    total_ects_required: int = Field(..., gt=0, description="Total ECTS required for graduation (positive integer)")
    graduation_conditions: Optional[str] = Field(None, description="Graduation conditions text")
    graduation_conditions_de: Optional[str] = Field(None, description="German graduation conditions text")


class AcademicTrackCreate(AcademicTrackBase):
    """Schema for creating a new academic track"""
    pass


class AcademicTrackUpdate(BaseModel):
    """Schema for updating an academic track (all fields optional)"""
    study_program_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    level: Optional[TrackLevel] = None
    description: Optional[str] = None
    description_de: Optional[str] = None
    total_ects_required: Optional[int] = Field(None, gt=0)
    graduation_conditions: Optional[str] = None
    graduation_conditions_de: Optional[str] = None


class AcademicTrackResponse(AcademicTrackBase):
    """Schema for academic track response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ==================== Semester Schemas ====================

class SemesterBase(BaseModel):
    """Base schema for Semester"""
    academic_track_id: int = Field(..., description="ID of the academic track this semester belongs to")
    name: str = Field(..., min_length=1, max_length=100, description="Semester name (e.g., 'S1', 'S2')")
    name_de: Optional[str] = Field(None, max_length=100, description="German semester name")
    semester_number: int = Field(..., ge=1, le=10, description="Semester number (1-10)")
    description: Optional[str] = Field(None, description="Semester description")
    description_de: Optional[str] = Field(None, description="German semester description")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS required for this semester (0 or positive)")


class SemesterCreate(SemesterBase):
    """Schema for creating a new semester"""
    pass


class SemesterUpdate(BaseModel):
    """Schema for updating a semester (all fields optional)"""
    academic_track_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_de: Optional[str] = Field(None, max_length=100)
    semester_number: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None
    description_de: Optional[str] = None
    ects_required: Optional[int] = Field(None, ge=0)


class SemesterResponse(SemesterBase):
    """Schema for semester response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ==================== Teaching Unit Schemas ====================

class TeachingUnitBase(BaseModel):
    """Base schema for TeachingUnit"""
    semester_id: int = Field(..., description="ID of the semester this teaching unit belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Teaching unit name (1-255 characters)")
    name_de: Optional[str] = Field(None, max_length=255, description="German teaching unit name")
    code: Optional[str] = Field(None, max_length=50, description="Teaching unit code (e.g., 'UE1', 'UE2')")
    description: Optional[str] = Field(None, description="Teaching unit description")
    description_de: Optional[str] = Field(None, description="German teaching unit description")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS required for this teaching unit (0 or positive)")


class TeachingUnitCreate(TeachingUnitBase):
    """Schema for creating a new teaching unit"""
    pass


class TeachingUnitUpdate(BaseModel):
    """Schema for updating a teaching unit (all fields optional)"""
    semester_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    description_de: Optional[str] = None
    ects_required: Optional[int] = Field(None, ge=0)


class TeachingUnitResponse(TeachingUnitBase):
    """Schema for teaching unit response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ==================== Course Schemas ====================

class CourseBase(BaseModel):
    """Base schema for Course"""
    semester_id: int = Field(..., description="ID of the semester this course belongs to")
    teaching_unit_id: Optional[int] = Field(None, description="ID of the teaching unit (optional)")
    name: str = Field(..., min_length=1, max_length=255, description="Course name (1-255 characters)")
    name_de: Optional[str] = Field(None, max_length=255, description="German course name")
    code: Optional[str] = Field(None, max_length=50, description="Course code (e.g., 'CS101', 'MATH201')")
    description: Optional[str] = Field(None, description="Course description")
    description_de: Optional[str] = Field(None, description="German course description")
    ects_credits: int = Field(..., ge=1, le=30, description="ECTS credits (1-30 range)")
    coefficient: float = Field(..., ge=0.1, le=10.0, description="Coefficient/weight in grade calculations (0.1-10.0 range)")
    difficulty_level: int = Field(..., ge=1, le=5, description="Difficulty level (1-5 range)")


class CourseCreate(CourseBase):
    """Schema for creating a new course"""
    prerequisite_ids: Optional[List[int]] = Field(default=[], description="List of prerequisite course IDs")


class CourseUpdate(BaseModel):
    """Schema for updating a course (all fields optional)"""
    semester_id: Optional[int] = None
    teaching_unit_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    description_de: Optional[str] = None
    ects_credits: Optional[int] = Field(None, ge=1, le=30)
    coefficient: Optional[float] = Field(None, ge=0.1, le=10.0)
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)


class CourseResponse(CourseBase):
    """Schema for course response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class CourseWithPrerequisitesResponse(CourseResponse):
    """Schema for course response with prerequisite details"""
    prerequisites: List[CourseResponse] = Field(default=[], description="List of prerequisite courses")


# ==================== List Response Schemas ====================

class AcademicTrackListResponse(BaseModel):
    """Schema for list of academic tracks"""
    tracks: List[AcademicTrackResponse]
    total: int


class SemesterListResponse(BaseModel):
    """Schema for list of semesters"""
    semesters: List[SemesterResponse]
    total: int


class TeachingUnitListResponse(BaseModel):
    """Schema for list of teaching units"""
    teaching_units: List[TeachingUnitResponse]
    total: int


class CourseListResponse(BaseModel):
    """Schema for list of courses"""
    courses: List[CourseResponse]
    total: int
