"""
Admin schemas for Super Admin Platform
Schemas for managing universities, study programs, campuses, and related entities
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


# ============================================================================
# German Text Validation Utility
# ============================================================================

def validate_german_text(text: Optional[str], field_name: str) -> Optional[str]:
    """
    Validate that text supports German special characters (ä, ö, ü, ß).
    
    Args:
        text: The text to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated text
        
    Raises:
        ValueError: If text contains invalid characters
    """
    if text is None:
        return None
    
    # Strip whitespace and check if empty
    if not text.strip():
        return text
    
    # Allow alphanumeric, spaces, common punctuation, and German special characters
    # Pattern allows: letters (including German), numbers, spaces, and extended punctuation
    german_pattern = re.compile(r'^[a-zA-ZäöüßÄÖÜ0-9\s\.,\-\(\)\/\':;&!?%@#+\*\[\]]+$')
    
    if not german_pattern.match(text):
        raise ValueError(f"{field_name} contains invalid characters. Allowed: letters (including ä, ö, ü, ß), numbers, spaces, and common punctuation")
    
    return text


# ============================================================================
# University Schemas
# ============================================================================

class UniversityBase(BaseModel):
    """Base schema for University with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="University name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="University name in German")
    country: str = Field(default="Germany", max_length=100, description="Country where university is located")
    description: Optional[str] = Field(None, description="University description in English")
    description_de: Optional[str] = Field(None, description="University description in German")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate university names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class UniversityCreate(UniversityBase):
    """Schema for creating a new university"""
    pass


class UniversityUpdate(BaseModel):
    """Schema for updating a university (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="University name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="University name in German")
    country: Optional[str] = Field(None, max_length=100, description="Country where university is located")
    description: Optional[str] = Field(None, description="University description in English")
    description_de: Optional[str] = Field(None, description="University description in German")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate university names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class UniversityResponse(UniversityBase):
    """Schema for university response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class UniversityListResponse(BaseModel):
    """Schema for list of universities"""
    universities: List[UniversityResponse]
    total: int


class UniversityWithCampusesResponse(UniversityResponse):
    """Schema for university response with campus details"""
    campuses: List['CampusResponse'] = Field(default=[], description="List of campuses for this university")


class UniversityDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting a university"""
    campuses_count: int = Field(..., description="Number of campuses linked to this university")
    study_programs_count: int = Field(..., description="Number of study programs linked to this university")
    academic_tracks_count: int = Field(..., description="Number of academic tracks linked through programs")
    courses_count: int = Field(..., description="Number of courses linked through programs")


# ============================================================================
# Campus Schemas
# ============================================================================

class CampusBase(BaseModel):
    """Base schema for Campus with common fields"""
    university_id: int = Field(..., gt=0, description="ID of the university this campus belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Campus name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Campus name in German")
    location: Optional[str] = Field(None, max_length=255, description="City or address of the campus")
    description: Optional[str] = Field(None, description="Campus description in English")
    description_de: Optional[str] = Field(None, description="Campus description in German")
    
    @field_validator('name', 'name_de', 'location')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class CampusCreate(CampusBase):
    """Schema for creating a new campus"""
    pass


class CampusUpdate(BaseModel):
    """Schema for updating a campus (all fields optional)"""
    university_id: Optional[int] = Field(None, gt=0, description="ID of the university this campus belongs to")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Campus name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Campus name in German")
    location: Optional[str] = Field(None, max_length=255, description="City or address of the campus")
    description: Optional[str] = Field(None, description="Campus description in English")
    description_de: Optional[str] = Field(None, description="Campus description in German")
    
    @field_validator('name', 'name_de', 'location')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class CampusResponse(CampusBase):
    """Schema for campus response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class CampusListResponse(BaseModel):
    """Schema for list of campuses"""
    campuses: List[CampusResponse]
    total: int


# ============================================================================
# Study Program Schemas
# ============================================================================

class StudyProgramBase(BaseModel):
    """Base schema for Study Program with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Study program name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Study program name in German (primary language)")
    description: Optional[str] = Field(None, description="Study program description in English")
    description_de: Optional[str] = Field(None, description="Study program description in German")
    code: Optional[str] = Field(None, max_length=50, description="Program code (e.g., CS, MED, LAW)")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate program names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate program code format (uppercase letters and numbers only)"""
        if v is not None and v != "":
            if not re.match(r'^[A-Z0-9]+$', v):
                raise ValueError("Program code must contain only uppercase letters and numbers")
        return v


class StudyProgramCreate(StudyProgramBase):
    """Schema for creating a new study program"""
    pass


class StudyProgramUpdate(BaseModel):
    """Schema for updating a study program (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Study program name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Study program name in German")
    description: Optional[str] = Field(None, description="Study program description in English")
    description_de: Optional[str] = Field(None, description="Study program description in German")
    code: Optional[str] = Field(None, max_length=50, description="Program code (e.g., CS, MED, LAW)")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate program names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate program code format (uppercase letters and numbers only)"""
        if v is not None and v != "":
            if not re.match(r'^[A-Z0-9]+$', v):
                raise ValueError("Program code must contain only uppercase letters and numbers")
        return v


class StudyProgramResponse(StudyProgramBase):
    """Schema for study program response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class StudyProgramListResponse(BaseModel):
    """Schema for list of study programs"""
    programs: List[StudyProgramResponse]
    total: int


class StudyProgramWithUniversitiesResponse(StudyProgramResponse):
    """Schema for study program response with linked universities"""
    universities: List[UniversityResponse] = Field(default=[], description="List of universities offering this program")


class StudyProgramDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting a study program"""
    academic_tracks_count: int = Field(..., description="Number of academic tracks linked to this program")
    courses_count: int = Field(..., description="Number of courses linked through academic tracks")


# ============================================================================
# Academic Track Schemas
# ============================================================================

class AcademicTrackBase(BaseModel):
    """Base schema for Academic Track with common fields"""
    study_program_id: int = Field(..., gt=0, description="ID of the study program this track belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Academic track name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Academic track name in German")
    level: str = Field(..., description="Academic level: bachelor, master, or doctorate")
    description: Optional[str] = Field(None, description="Track description in English")
    description_de: Optional[str] = Field(None, description="Track description in German")
    total_ects_required: int = Field(..., gt=0, description="Total ECTS required for graduation")
    graduation_conditions: Optional[str] = Field(None, description="Graduation conditions in English")
    graduation_conditions_de: Optional[str] = Field(None, description="Graduation conditions in German")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate track names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de', 'graduation_conditions', 'graduation_conditions_de')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate level is one of the allowed values"""
        allowed_levels = ["bachelor", "master", "doctorate"]
        if v not in allowed_levels:
            raise ValueError(f"Level must be one of: {', '.join(allowed_levels)}")
        return v
    
    @field_validator('total_ects_required')
    @classmethod
    def validate_ects(cls, v: int) -> int:
        """Validate ECTS requirements are positive integers"""
        if v <= 0:
            raise ValueError("Total ECTS required must be a positive integer")
        return v


class AcademicTrackCreate(AcademicTrackBase):
    """Schema for creating a new academic track"""
    pass


class AcademicTrackUpdate(BaseModel):
    """Schema for updating an academic track (all fields optional)"""
    study_program_id: Optional[int] = Field(None, gt=0, description="ID of the study program this track belongs to")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Academic track name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Academic track name in German")
    level: Optional[str] = Field(None, description="Academic level: bachelor, master, or doctorate")
    description: Optional[str] = Field(None, description="Track description in English")
    description_de: Optional[str] = Field(None, description="Track description in German")
    total_ects_required: Optional[int] = Field(None, gt=0, description="Total ECTS required for graduation")
    graduation_conditions: Optional[str] = Field(None, description="Graduation conditions in English")
    graduation_conditions_de: Optional[str] = Field(None, description="Graduation conditions in German")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate track names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de', 'graduation_conditions', 'graduation_conditions_de')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate level is one of the allowed values"""
        if v is not None:
            allowed_levels = ["bachelor", "master", "doctorate"]
            if v not in allowed_levels:
                raise ValueError(f"Level must be one of: {', '.join(allowed_levels)}")
        return v
    
    @field_validator('total_ects_required')
    @classmethod
    def validate_ects(cls, v: Optional[int]) -> Optional[int]:
        """Validate ECTS requirements are positive integers"""
        if v is not None and v <= 0:
            raise ValueError("Total ECTS required must be a positive integer")
        return v


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


class AcademicTrackListResponse(BaseModel):
    """Schema for list of academic tracks"""
    tracks: List[AcademicTrackResponse]
    total: int


class AcademicTrackDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting an academic track"""
    semesters_count: int = Field(..., description="Number of semesters linked to this track")
    courses_count: int = Field(..., description="Number of courses linked through semesters")


# ============================================================================
# Semester Schemas
# ============================================================================

class SemesterBase(BaseModel):
    """Base schema for Semester with common fields"""
    academic_track_id: int = Field(..., gt=0, description="ID of the academic track this semester belongs to")
    name: str = Field(..., min_length=1, max_length=100, description="Semester name (e.g., S1, S2, S3)")
    name_de: Optional[str] = Field(None, max_length=100, description="Semester name in German")
    semester_number: int = Field(..., ge=1, le=6, description="Semester number (1-6 for Bachelor, 1-4 for Master)")
    description: Optional[str] = Field(None, description="Semester description in English")
    description_de: Optional[str] = Field(None, description="Semester description in German")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS requirements for this semester")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate semester names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('ects_required')
    @classmethod
    def validate_ects(cls, v: Optional[int]) -> Optional[int]:
        """Validate ECTS requirements are non-negative"""
        if v is not None and v < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        return v


class SemesterCreate(SemesterBase):
    """Schema for creating a new semester"""
    pass


class SemesterUpdate(BaseModel):
    """Schema for updating a semester (all fields optional)"""
    academic_track_id: Optional[int] = Field(None, gt=0, description="ID of the academic track this semester belongs to")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Semester name (e.g., S1, S2, S3)")
    name_de: Optional[str] = Field(None, max_length=100, description="Semester name in German")
    semester_number: Optional[int] = Field(None, ge=1, le=6, description="Semester number (1-6 for Bachelor, 1-4 for Master)")
    description: Optional[str] = Field(None, description="Semester description in English")
    description_de: Optional[str] = Field(None, description="Semester description in German")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS requirements for this semester")
    
    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate semester names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('ects_required')
    @classmethod
    def validate_ects(cls, v: Optional[int]) -> Optional[int]:
        """Validate ECTS requirements are non-negative"""
        if v is not None and v < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        return v


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


class SemesterListResponse(BaseModel):
    """Schema for list of semesters"""
    semesters: List[SemesterResponse]
    total: int


class SemesterDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting a semester"""
    teaching_units_count: int = Field(..., description="Number of teaching units linked to this semester")
    courses_count: int = Field(..., description="Number of courses linked to this semester")


# ============================================================================
# Teaching Unit Schemas
# ============================================================================

class TeachingUnitBase(BaseModel):
    """Base schema for Teaching Unit with common fields"""
    semester_id: int = Field(..., gt=0, description="ID of the semester this teaching unit belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Teaching unit name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Teaching unit name in German")
    code: Optional[str] = Field(None, max_length=50, description="Teaching unit code (e.g., UE1, UE2)")
    description: Optional[str] = Field(None, description="Teaching unit description in English")
    description_de: Optional[str] = Field(None, description="Teaching unit description in German")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS requirements for this teaching unit")
    
    @field_validator('name', 'name_de', 'code')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate teaching unit names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('ects_required')
    @classmethod
    def validate_ects(cls, v: Optional[int]) -> Optional[int]:
        """Validate ECTS requirements are non-negative"""
        if v is not None and v < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        return v


class TeachingUnitCreate(TeachingUnitBase):
    """Schema for creating a new teaching unit"""
    pass


class TeachingUnitUpdate(BaseModel):
    """Schema for updating a teaching unit (all fields optional)"""
    semester_id: Optional[int] = Field(None, gt=0, description="ID of the semester this teaching unit belongs to")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Teaching unit name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Teaching unit name in German")
    code: Optional[str] = Field(None, max_length=50, description="Teaching unit code (e.g., UE1, UE2)")
    description: Optional[str] = Field(None, description="Teaching unit description in English")
    description_de: Optional[str] = Field(None, description="Teaching unit description in German")
    ects_required: Optional[int] = Field(None, ge=0, description="ECTS requirements for this teaching unit")
    
    @field_validator('name', 'name_de', 'code')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate teaching unit names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v
    
    @field_validator('ects_required')
    @classmethod
    def validate_ects(cls, v: Optional[int]) -> Optional[int]:
        """Validate ECTS requirements are non-negative"""
        if v is not None and v < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        return v


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


class TeachingUnitListResponse(BaseModel):
    """Schema for list of teaching units"""
    teaching_units: List[TeachingUnitResponse]
    total: int


class TeachingUnitDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting a teaching unit"""
    courses_count: int = Field(..., description="Number of courses linked to this teaching unit")


# ============================================================================
# Course Schemas
# ============================================================================

class CourseBase(BaseModel):
    """Base schema for Course with common fields"""
    semester_id: int = Field(..., gt=0, description="ID of the semester this course belongs to")
    teaching_unit_id: Optional[int] = Field(None, gt=0, description="ID of the teaching unit (optional)")
    name: str = Field(..., min_length=1, max_length=255, description="Course name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Course name in German")
    code: Optional[str] = Field(None, max_length=50, description="Course code (e.g., CS101, MATH201)")
    description: Optional[str] = Field(None, description="Course description in English")
    description_de: Optional[str] = Field(None, description="Course description in German")
    ects_credits: int = Field(..., ge=1, le=30, description="ECTS credits (1-30)")
    coefficient: float = Field(..., ge=0.1, le=10.0, description="Course weight in grade calculations (0.1-10.0)")
    difficulty_level: int = Field(..., ge=1, le=5, description="Difficulty level (1-5)")

    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate course names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('ects_credits')
    @classmethod
    def validate_ects(cls, v: int) -> int:
        """Validate ECTS credits are within the allowed range (1-30)"""
        if v < 1 or v > 30:
            raise ValueError("ECTS credits must be an integer between 1 and 30")
        return v

    @field_validator('coefficient')
    @classmethod
    def validate_coefficient(cls, v: float) -> float:
        """Validate coefficient is within the allowed range (0.1-10.0)"""
        if v < 0.1 or v > 10.0:
            raise ValueError("Coefficient must be a number between 0.1 and 10.0")
        return round(v, 2)

    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v: int) -> int:
        """Validate difficulty level is within the allowed range (1-5)"""
        if v < 1 or v > 5:
            raise ValueError("Difficulty level must be an integer between 1 and 5")
        return v


class CourseCreate(CourseBase):
    """Schema for creating a new course"""
    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course (all fields optional)"""
    semester_id: Optional[int] = Field(None, gt=0, description="ID of the semester this course belongs to")
    teaching_unit_id: Optional[int] = Field(None, gt=0, description="ID of the teaching unit (optional)")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Course name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Course name in German")
    code: Optional[str] = Field(None, max_length=50, description="Course code (e.g., CS101, MATH201)")
    description: Optional[str] = Field(None, description="Course description in English")
    description_de: Optional[str] = Field(None, description="Course description in German")
    ects_credits: Optional[int] = Field(None, ge=1, le=30, description="ECTS credits (1-30)")
    coefficient: Optional[float] = Field(None, ge=0.1, le=10.0, description="Course weight in grade calculations (0.1-10.0)")
    difficulty_level: Optional[int] = Field(None, ge=1, le=5, description="Difficulty level (1-5)")

    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate course names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('description', 'description_de')
    @classmethod
    def validate_descriptions(cls, v: Optional[str], info) -> Optional[str]:
        """Validate descriptions support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('coefficient')
    @classmethod
    def validate_coefficient(cls, v: Optional[float]) -> Optional[float]:
        """Validate coefficient is within the allowed range (0.1-10.0)"""
        if v is not None:
            return round(v, 2)
        return v


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


class CourseListResponse(BaseModel):
    """Schema for paginated list of courses"""
    courses: List[CourseResponse]
    total: int


class CoursePrerequisiteInfo(BaseModel):
    """Lightweight course info used inside prerequisite/dependent lists"""
    id: int
    name: str
    name_de: Optional[str]
    code: Optional[str]
    ects_credits: int
    difficulty_level: int
    semester_id: int

    model_config = {
        "from_attributes": True
    }


class CoursePrerequisitesResponse(BaseModel):
    """Schema for course prerequisites list response"""
    course_id: int
    prerequisites: List[CoursePrerequisiteInfo]
    total: int


class CourseDependentsResponse(BaseModel):
    """Schema for courses that depend on a given course (reverse prerequisite lookup)"""
    course_id: int
    dependents: List[CoursePrerequisiteInfo]
    total: int


class CourseDependentCountsResponse(BaseModel):
    """Schema for dependent entity counts when deleting a course"""
    prerequisite_of_count: int = Field(..., description="Number of courses that list this course as a prerequisite")
    has_prerequisites_count: int = Field(..., description="Number of courses this course requires as prerequisites")


# ---------- Batch operation schemas ----------

class CourseBatchCreateItem(CourseBase):
    """Single item for batch course creation"""
    pass


class CourseBatchUpdateItem(CourseUpdate):
    """Single item for batch course update — must include the course id"""
    id: int = Field(..., gt=0, description="ID of the course to update")


class CourseBatchDeleteItem(BaseModel):
    """Single item for batch course deletion"""
    id: int = Field(..., gt=0, description="ID of the course to delete")


class CourseBatchOperation(BaseModel):
    """
    Batch operations for courses.

    Provide exactly one of: create_items, update_items, or delete_items.
    Mixed operation types in a single request are not supported.
    """
    operation: str = Field(
        ...,
        description="Batch operation type: 'create', 'update', or 'delete'"
    )
    create_items: Optional[List[CourseBatchCreateItem]] = Field(
        None, description="List of courses to create (used when operation='create')"
    )
    update_items: Optional[List[CourseBatchUpdateItem]] = Field(
        None, description="List of courses to update (used when operation='update')"
    )
    delete_ids: Optional[List[int]] = Field(
        None, description="List of course IDs to delete (used when operation='delete')"
    )

    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate batch operation type"""
        allowed = ["create", "update", "delete"]
        if v not in allowed:
            raise ValueError(f"Operation must be one of: {', '.join(allowed)}")
        return v


class CourseBatchErrorDetail(BaseModel):
    """Detail for a single failed item in a batch operation"""
    index: Optional[int] = None
    course_id: Optional[int] = None
    error: str


class CourseBatchResponse(BaseModel):
    """Response schema for batch course operations"""
    operation: str
    success_count: int
    error_count: int
    created_ids: Optional[List[int]] = None   # Only populated for 'create' operations
    errors: List[CourseBatchErrorDetail] = Field(default_factory=list)


# ============================================================================
# Prerequisite Relationship Schemas
# ============================================================================

class PrerequisiteCreate(BaseModel):
    """Schema for creating a new prerequisite relationship between two courses"""
    course_id: int = Field(..., gt=0, description="ID of the course that requires the prerequisite")
    prerequisite_id: int = Field(..., gt=0, description="ID of the course that must be completed first")

    @field_validator('prerequisite_id')
    @classmethod
    def validate_not_self_referencing(cls, v: int, info) -> int:
        """Validate that a course is not set as its own prerequisite"""
        course_id = info.data.get('course_id')
        if course_id is not None and v == course_id:
            raise ValueError("A course cannot be its own prerequisite")
        return v


class PrerequisiteResponse(BaseModel):
    """Schema for a single prerequisite relationship record"""
    id: int
    course_id: int
    prerequisite_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class PrerequisiteListResponse(BaseModel):
    """Schema for a paginated list of prerequisite relationships"""
    prerequisites: List[PrerequisiteResponse]
    total: int


class PrerequisiteDeleteRequest(BaseModel):
    """Schema for deleting a prerequisite relationship by course/prerequisite pair"""
    course_id: int = Field(..., gt=0, description="ID of the course that has the prerequisite")
    prerequisite_id: int = Field(..., gt=0, description="ID of the prerequisite course to remove")


class PrerequisiteValidateRequest(BaseModel):
    """Schema for pre-flight validation of a proposed prerequisite relationship"""
    course_id: int = Field(..., gt=0, description="ID of the course that would require the prerequisite")
    prerequisite_id: int = Field(..., gt=0, description="ID of the proposed prerequisite course")


class PrerequisiteValidateResponse(BaseModel):
    """Response schema for prerequisite cycle-detection validation"""
    is_valid: bool = Field(..., description="True if the relationship can be safely created")
    course_id: int
    prerequisite_id: int
    error_message: Optional[str] = Field(
        None,
        description="Human-readable description of the circular dependency path when is_valid=False"
    )
    cycle_path: Optional[List[str]] = Field(
        None,
        description="Ordered list of course names forming the detected cycle (if any)"
    )


class PrerequisiteChainNode(BaseModel):
    """A single node in a course's prerequisite chain tree"""
    level: int = Field(..., description="Depth in the dependency tree (1 = direct prerequisite)")
    course_id: int
    course_name: str
    course_code: Optional[str]
    semester_number: int
    ects_credits: int
    required_by_id: int = Field(..., description="ID of the course that directly requires this one")
    required_by_name: str = Field(..., description="Name of the course that directly requires this one")


class PrerequisiteChainResponse(BaseModel):
    """Complete prerequisite chain for a course, organised by depth level"""
    course_id: int
    total_nodes: int = Field(..., description="Total number of prerequisite nodes across all levels")
    chain: List[PrerequisiteChainNode] = Field(
        ...,
        description="All direct and transitive prerequisites ordered by level then semester"
    )


# ============================================================================
# Validation Rule Schemas
# ============================================================================

class ValidationRuleBase(BaseModel):
    """Base schema for ValidationRule — fields shared by create and response"""
    academic_track_id: int = Field(..., gt=0, description="ID of the academic track this rule belongs to")
    rule_type: str = Field(
        ...,
        description="Rule type: 'semester_validation', 'year_progression', or 'graduation'"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Rule name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Rule name in German")
    description: Optional[str] = Field(None, description="Rule description in English")
    description_de: Optional[str] = Field(None, description="Rule description in German")
    minimum_ects: int = Field(..., gt=0, description="Minimum ECTS required to satisfy this rule")
    additional_conditions: Optional[str] = Field(
        None, description="Additional conditions text in English"
    )
    additional_conditions_de: Optional[str] = Field(
        None, description="Additional conditions text in German"
    )

    @field_validator('rule_type')
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        """Validate rule_type is one of the accepted values"""
        allowed = ["semester_validation", "year_progression", "graduation"]
        if v not in allowed:
            raise ValueError(f"rule_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('description', 'description_de', 'additional_conditions', 'additional_conditions_de')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class ValidationRuleCreate(ValidationRuleBase):
    """Schema for creating a new validation rule"""
    pass


class ValidationRuleUpdate(BaseModel):
    """Schema for updating a validation rule (all fields optional)"""
    academic_track_id: Optional[int] = Field(None, gt=0, description="ID of the academic track this rule belongs to")
    rule_type: Optional[str] = Field(None, description="Rule type: 'semester_validation', 'year_progression', or 'graduation'")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Rule name in English")
    name_de: Optional[str] = Field(None, max_length=255, description="Rule name in German")
    description: Optional[str] = Field(None, description="Rule description in English")
    description_de: Optional[str] = Field(None, description="Rule description in German")
    minimum_ects: Optional[int] = Field(None, gt=0, description="Minimum ECTS required to satisfy this rule")
    additional_conditions: Optional[str] = Field(None, description="Additional conditions text in English")
    additional_conditions_de: Optional[str] = Field(None, description="Additional conditions text in German")

    @field_validator('rule_type')
    @classmethod
    def validate_rule_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate rule_type is one of the accepted values"""
        if v is not None:
            allowed = ["semester_validation", "year_progression", "graduation"]
            if v not in allowed:
                raise ValueError(f"rule_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator('name', 'name_de')
    @classmethod
    def validate_names(cls, v: Optional[str], info) -> Optional[str]:
        """Validate names support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v

    @field_validator('description', 'description_de', 'additional_conditions', 'additional_conditions_de')
    @classmethod
    def validate_text_fields(cls, v: Optional[str], info) -> Optional[str]:
        """Validate text fields support German characters"""
        if v:
            return validate_german_text(v, info.field_name)
        return v


class ValidationRuleResponse(ValidationRuleBase):
    """Schema for validation rule response"""
    id: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ValidationRuleListResponse(BaseModel):
    """Schema for paginated list of validation rules"""
    rules: List[ValidationRuleResponse]
    total: int


class EctsHierarchyValidationResponse(BaseModel):
    """
    Response schema for ECTS hierarchy validation of an academic track.

    Validates that:  graduation_ects >= year_progression_ects >= semester_validation_ects
    """
    is_valid: bool
    track_id: int
    track_name: Optional[str]
    track_level: Optional[str]
    graduation_ects: Optional[int] = Field(None, description="ECTS required for graduation")
    year_progression_ects: Optional[int] = Field(None, description="ECTS required for year progression")
    semester_validation_ects: Optional[int] = Field(None, description="ECTS required for semester validation")
    errors: List[str] = Field(default_factory=list, description="List of hierarchy violation messages")


# ============================================================================
# Bulk Import Schemas
# ============================================================================

class ImportErrorDetail(BaseModel):
    """A single error or warning from import validation"""
    row: Optional[int] = Field(None, description="Row number in the Excel sheet (None = file-level error)")
    sheet: str = Field(..., description="Excel sheet name where the error occurred")
    message: str = Field(..., description="Human-readable error message")
    type: str = Field("validation", description="Error type: 'validation', 'circular_dependency', 'ects_mismatch', etc.")


class ImportEntityCount(BaseModel):
    """Count of entities for one entity type in a preview or result"""
    count: int
    samples: Optional[List[dict]] = Field(None, description="Up to 3 sample rows from the parsed data")


class ImportPreviewResponse(BaseModel):
    """
    Preview of changes that would result from executing an import.
    Generated after parse + validation — before any DB writes.
    """
    universities: ImportEntityCount
    campuses: ImportEntityCount
    programs: ImportEntityCount
    university_programs: ImportEntityCount
    tracks: ImportEntityCount
    semesters: ImportEntityCount
    teaching_units: ImportEntityCount
    courses: ImportEntityCount
    prerequisites: ImportEntityCount
    total_entities: int


class ImportValidateResponse(BaseModel):
    """Response from the validate step — reports errors per sheet and row"""
    is_valid: bool = Field(..., description="True when no errors are found")
    error_count: int
    warning_count: int = 0
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    entity_counts: Optional[dict] = Field(
        None, description="Entity counts from parsed data (available even when invalid)"
    )


class ImportExecuteResponse(BaseModel):
    """Summary returned after a successful transactional import"""
    success: bool
    message: str
    import_id: Optional[int] = Field(
        None, description="Audit log ID for this import (useful for rollback)"
    )
    created_counts: dict = Field(..., description="Number of each entity type created")
    total_created: int
    timestamp: str


class ImportHistoryItem(BaseModel):
    """Single item in the import history list"""
    id: int = Field(..., description="Audit log ID")
    user_id: Optional[int]
    timestamp: datetime
    description: Optional[str]
    created_counts: Optional[dict] = Field(
        None, description="Counts of created entities from the import"
    )

    model_config = {
        "from_attributes": True
    }


class ImportHistoryResponse(BaseModel):
    """Paginated list of past bulk imports"""
    imports: List[ImportHistoryItem]
    total: int


class ImportRollbackResponse(BaseModel):
    """Result of a rollback operation"""
    success: bool
    message: str
    import_id: int
    deleted_counts: dict = Field(default_factory=dict)
    total_deleted: int = 0


# ============================================================================
# Dashboard & Monitoring Schemas
# ============================================================================

class CurriculumStats(BaseModel):
    """Curriculum entity counts"""
    study_programs: int
    academic_tracks: int
    semesters: int
    teaching_units: int
    courses: int
    prerequisite_relationships: int


class StudentStats(BaseModel):
    """Student and plan counts"""
    total_students: int
    active_study_plans: int
    total_study_sessions: int


class AIGenerationStats(BaseModel):
    """AI plan generation statistics"""
    total_generations: int
    successful_generations: int
    failed_generations: int
    success_rate_pct: float
    avg_duration_seconds: Optional[float]


class ImportStats(BaseModel):
    """Bulk import history counts"""
    total_imports: int
    total_entities_imported: int


class DashboardStatsResponse(BaseModel):
    """
    Aggregate statistics response for the Super Admin dashboard.

    Requirements: 10.1-10.4, 10.8
    """
    # Structural entities
    universities: int
    campuses: int
    curriculum: CurriculumStats
    students: StudentStats
    ai_generations: AIGenerationStats
    imports: ImportStats

    # Recent activity counts (last 30 days)
    recent_admin_actions_30d: int

    generated_at: str = Field(..., description="ISO-8601 timestamp of when stats were computed")


class ActivityItem(BaseModel):
    """Single recent activity record from the audit log"""
    id: int
    entity_type: str
    entity_id: int
    operation: str = Field(..., description="'create', 'update', or 'delete'")
    user_id: Optional[int]
    user_email: Optional[str] = Field(None, description="Email of the user who performed the action")
    timestamp: datetime
    description: Optional[str]


class ActivityFeedResponse(BaseModel):
    """
    Paginated recent-activity feed from audit logs.

    Requirements: 10.5
    """
    activities: List[ActivityItem]
    total: int


class HealthCheckItem(BaseModel):
    """Result of a single health check probe"""
    name: str
    status: str = Field(..., description="'ok', 'warning', or 'error'")
    message: Optional[str] = None
    value: Optional[str] = Field(None, description="Measured value (e.g., '3.2 GB free')")


class SystemHealthResponse(BaseModel):
    """
    Overall system health status.

    Requirements: 10.6
    """
    status: str = Field(..., description="Overall status: 'ok', 'degraded', or 'error'")
    checks: List[HealthCheckItem]
    checked_at: str = Field(..., description="ISO-8601 timestamp of the health check")


# ============================================================================
# Audit Log Schemas (10.1)
# ============================================================================

class AuditLogResponse(BaseModel):
    """Schema for a single audit log entry"""
    id: int
    entity_type: str
    entity_id: int
    operation: str
    user_id: Optional[int]
    user_email: Optional[str] = None
    timestamp: datetime
    description: Optional[str]
    before_value: Optional[dict] = None
    after_value: Optional[dict] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class EntityHistoryResponse(BaseModel):
    """Full change history for a specific entity"""
    entity_type: str
    entity_id: int
    history: List[AuditLogResponse]
    total: int


# ============================================================================
# Export & Report Schemas (10.2)
# ============================================================================

class CurriculumSummaryItem(BaseModel):
    """One row in the curriculum summary report"""
    university: str
    program: str
    track: str
    track_level: str
    total_ects_required: int
    semester_count: int
    course_count: int
    teaching_unit_count: int


class CurriculumSummaryReport(BaseModel):
    """Curriculum summary report — one row per academic track"""
    generated_at: str
    generated_by: Optional[str]
    rows: List[CurriculumSummaryItem]
    total_tracks: int


class PrerequisiteChainReportItem(BaseModel):
    """One prerequisite relationship for the report"""
    course_id: int
    course_name: str
    course_code: Optional[str]
    semester_number: int
    prerequisite_id: int
    prerequisite_name: str
    prerequisite_code: Optional[str]
    prerequisite_semester_number: int


class PrerequisiteChainReport(BaseModel):
    """Prerequisite relationships report across all active courses"""
    generated_at: str
    generated_by: Optional[str]
    relationships: List[PrerequisiteChainReportItem]
    total_relationships: int


# ============================================================================
# Search Schemas (10.3)
# ============================================================================

class SearchResultItem(BaseModel):
    """A single search result hit"""
    entity_type: str = Field(..., description="E.g. 'university', 'course', 'program'")
    id: int
    name: str
    name_de: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    match_field: str = Field(..., description="Which field matched the query")
    relevance: int = Field(1, description="Relevance score (higher = better match)")


class SearchResponse(BaseModel):
    """Global search response grouped by entity type"""
    query: str
    total_hits: int
    results_by_type: dict = Field(..., description="Dict of entity_type → list of SearchResultItem")
    search_duration_ms: Optional[float] = None


# ============================================================================
# Role Management Schemas (11.1)
# ============================================================================

class AdminRoleResponse(BaseModel):
    """A system admin role definition"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserRoleResponse(BaseModel):
    """A single user-to-role assignment"""
    id: int
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    role_display_name: Optional[str] = None
    university_id: Optional[int] = None
    program_id: Optional[int] = None
    assigned_at: datetime
    assigned_by: Optional[int] = None

    model_config = {"from_attributes": True}


class RoleAssignRequest(BaseModel):
    """Request body for assigning a role to a user"""
    user_id: int = Field(..., gt=0, description="ID of the user to assign the role to")
    role_name: str = Field(
        ...,
        description="Role to assign: 'super_admin', 'university_admin', or 'program_coordinator'",
    )
    university_id: Optional[int] = Field(
        None,
        gt=0,
        description="Required when role_name='university_admin'",
    )
    program_id: Optional[int] = Field(
        None,
        gt=0,
        description="Required when role_name='program_coordinator'",
    )

    @field_validator("role_name")
    @classmethod
    def validate_role_name(cls, v: str) -> str:
        allowed = ["super_admin", "university_admin", "program_coordinator"]
        if v not in allowed:
            raise ValueError(f"role_name must be one of: {', '.join(allowed)}")
        return v


class RoleUpdateRequest(BaseModel):
    """Request body for modifying an existing role assignment"""
    role_name: Optional[str] = Field(None, description="New role name")
    university_id: Optional[int] = Field(None, gt=0)
    program_id: Optional[int] = Field(None, gt=0)

    @field_validator("role_name")
    @classmethod
    def validate_role_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = ["super_admin", "university_admin", "program_coordinator"]
            if v not in allowed:
                raise ValueError(f"role_name must be one of: {', '.join(allowed)}")
        return v


class RoleListResponse(BaseModel):
    """Paginated list of user role assignments"""
    assignments: List[UserRoleResponse]
    total: int


class AdminRoleListResponse(BaseModel):
    """List of all available admin role definitions"""
    roles: List[AdminRoleResponse]


# ============================================================================
# System Settings Schemas (11.2)
# ============================================================================

class SystemSettingItem(BaseModel):
    """A single system setting key-value pair"""
    key: str = Field(..., description="Setting key (unique identifier)")
    value: str = Field(..., description="Setting value (always stored as string)")
    description: Optional[str] = Field(None, description="Human-readable description of the setting")
    category: str = Field("general", description="Setting category: 'ects', 'security', 'files', 'session'")
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class SystemSettingsResponse(BaseModel):
    """All system settings grouped by category"""
    settings: List[SystemSettingItem]
    total: int
    generated_at: str


class SystemSettingsUpdateRequest(BaseModel):
    """Request body for updating one or more system settings"""
    updates: dict = Field(
        ...,
        description="Dict of setting_key → new_value (all values treated as strings)",
    )

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: dict) -> dict:
        if not v:
            raise ValueError("updates dict must not be empty")
        # Validate all keys are strings
        for key in v:
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Invalid setting key: {key!r}")
        return v


# Update forward references for nested models
UniversityWithCampusesResponse.model_rebuild()

