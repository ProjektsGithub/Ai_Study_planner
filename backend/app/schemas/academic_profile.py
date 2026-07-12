"""
Pydantic schemas for Academic Profile management.

Covers university → filière → cursus → semester hierarchy
linked to the Super Admin Platform reference data.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Reference data schemas (fetched from Super Admin Platform)
# ---------------------------------------------------------------------------

class UniversityResponse(BaseModel):
    """University reference data from Super Admin Platform"""
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FiliereResponse(BaseModel):
    """Filière (study program) reference data"""
    id: int
    name: str
    code: Optional[str] = None
    university_id: int

    model_config = ConfigDict(from_attributes=True)


class CursusResponse(BaseModel):
    """Cursus (academic track) reference data"""
    id: int
    name: str
    code: Optional[str] = None
    filiere_id: int
    total_ects: Optional[float] = None
    duration_semesters: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SemesterInfo(BaseModel):
    """Basic semester info within a semester structure"""
    id: int
    number: int
    name: Optional[str] = None
    ects_required: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class SemesterStructure(BaseModel):
    """Complete semester structure for a cursus"""
    cursus_id: int
    cursus_name: str
    total_ects: Optional[float] = None
    semesters: List[SemesterInfo] = []


# ---------------------------------------------------------------------------
# Academic Profile update / response schemas
# ---------------------------------------------------------------------------

class AcademicProfileUpdate(BaseModel):
    """Schema for updating the academic profile fields on StudentProfile"""
    university_id: Optional[int] = Field(
        None,
        description="ID of the university from Super Admin Platform"
    )
    filiere_id: Optional[int] = Field(
        None,
        description="ID of the study program (filière) from Super Admin Platform"
    )
    cursus_id: Optional[int] = Field(
        None,
        description="ID of the academic track (cursus) from Super Admin Platform"
    )
    current_semester: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Current semester number (1–20)"
    )
    academic_year: Optional[int] = Field(
        None,
        ge=2000,
        le=2100,
        description="Academic year of enrollment (e.g. 2024)"
    )


class AcademicProfileResponse(BaseModel):
    """Academic profile fields returned to the client"""
    university_id: Optional[int] = None
    filiere_id: Optional[int] = None
    cursus_id: Optional[int] = None
    current_semester: Optional[int] = None
    academic_year: Optional[int] = None

    # Resolved names (populated by service layer)
    university_name: Optional[str] = None
    filiere_name: Optional[str] = None
    cursus_name: Optional[str] = None

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
