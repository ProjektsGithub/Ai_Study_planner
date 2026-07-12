"""
Academic Profile API Endpoints

GET  /api/v1/academic/universities              — list all universities
GET  /api/v1/academic/filieres?university_id=   — programs for a university
GET  /api/v1/academic/cursus?filiere_id=        — tracks for a program
GET  /api/v1/academic/semester-structure?cursus_id= — semester structure
GET  /api/v1/academic/profile                   — current user's academic profile
PUT  /api/v1/academic/profile                   — update academic profile

Requirements: 16.1, 16.2, 16.13–16.17, 18.1
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.academic_profile import (
    AcademicProfileUpdate,
    AcademicProfileResponse,
    UniversityResponse,
    FiliereResponse,
    CursusResponse,
    SemesterStructure,
)
from app.services.academic_profile_service import academic_profile_service

router = APIRouter(prefix="/academic", tags=["Academic Profile"])


@router.get(
    "/universities",
    response_model=List[UniversityResponse],
    summary="List all universities",
)
async def get_universities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all active universities from the Super Admin Platform.

    Results are cached for 24 hours.
    """
    return academic_profile_service.get_universities(db)


@router.get(
    "/filieres",
    response_model=List[FiliereResponse],
    summary="List study programs for a university",
)
async def get_filieres(
    university_id: int = Query(..., description="University ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all study programs (filières) for the given university.

    Returns 404 if university_id is invalid.
    """
    return academic_profile_service.get_filieres(db, university_id)


@router.get(
    "/cursus",
    response_model=List[CursusResponse],
    summary="List academic tracks for a study program",
)
async def get_cursus(
    filiere_id: int = Query(..., description="Study program (filière) ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all academic tracks (cursus) for the given study program.

    Returns 404 if filiere_id has no tracks.
    """
    return academic_profile_service.get_cursus_options(db, filiere_id)


@router.get(
    "/semester-structure",
    response_model=SemesterStructure,
    summary="Get semester structure for a cursus",
)
async def get_semester_structure(
    cursus_id: int = Query(..., description="Academic track (cursus) ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the complete semester structure (semesters + ECTS) for a cursus.

    Returns 404 if cursus_id is invalid.
    """
    return academic_profile_service.get_semester_structure(db, cursus_id)


@router.get(
    "/profile",
    response_model=AcademicProfileResponse,
    summary="Get current user's academic profile",
)
async def get_academic_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the academic profile fields (university, filière, cursus, semester)
    for the authenticated student, with human-readable names resolved.

    Returns 404 if no student profile exists.
    """
    return academic_profile_service.get_academic_profile(db, current_user.id)


@router.put(
    "/profile",
    response_model=AcademicProfileResponse,
    summary="Update academic profile",
)
async def update_academic_profile(
    profile_data: AcademicProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the academic profile fields for the authenticated student.

    Validates that:
    - university_id exists in the Super Admin Platform
    - filiere_id belongs to the given university
    - cursus_id belongs to the given filière

    Returns 400 for invalid IDs, 404 if no student profile exists.
    """
    return academic_profile_service.update_academic_profile(
        db, current_user.id, profile_data
    )
