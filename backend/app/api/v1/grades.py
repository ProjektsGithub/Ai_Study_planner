"""
Grade API Endpoints

GET  /api/v1/grades                   — all grades for authenticated user
GET  /api/v1/grades/history           — grade history for a course
GET  /api/v1/grades/failed            — only failed courses
POST /api/v1/grades                   — create / update grade (auto validation status)
PUT  /api/v1/grades/{grade_id}        — update existing grade by ID

Requirements: 16.4, 16.5, 16.13–16.17, 20.1, 20.2, 20.8
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse, GradeListResponse
from app.services.grade_service import grade_service

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.get(
    "",
    response_model=GradeListResponse,
    summary="Get all grades for the authenticated student",
)
async def get_grades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all grade entries for the authenticated student.

    The latest attempt per course is returned first.
    Includes validation_status (validated | failed | in_progress).
    """
    grades = grade_service.get_grades_by_user(db, current_user.id)
    return GradeListResponse(grades=grades, total=len(grades))


@router.get(
    "/failed",
    response_model=GradeListResponse,
    summary="Get only failed grades",
)
async def get_failed_grades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all grades with validation_status='failed' for the authenticated student.
    """
    grades = grade_service.get_failed_grades(db, current_user.id)
    return GradeListResponse(grades=grades, total=len(grades))


@router.get(
    "/history",
    response_model=GradeListResponse,
    summary="Get grade history for a course",
)
async def get_grade_history(
    course_id: int = Query(..., description="Course ID to get grade history for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all grade attempts for a specific course, ordered by attempt_number ascending.

    Useful to track student progress across retakes.
    """
    grades = grade_service.get_grade_history(db, current_user.id, course_id)
    return GradeListResponse(grades=grades, total=len(grades))


@router.post(
    "",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a grade",
)
async def create_grade(
    grade_data: GradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new grade entry or update an existing attempt.

    If a grade for (course_id, attempt_number) already exists, it is updated.
    validation_status is calculated automatically:
    - **in_progress** — no grade_obtained provided
    - **validated** — grade_obtained >= min_passing_grade
    - **failed** — grade_obtained < min_passing_grade

    Triggers ECTS recalculation when status changes to 'validated'.
    Triggers study plan regeneration when grade changes.

    Validation:
    - grade_obtained must be between 0 and max_grade
    - min_passing_grade must be positive
    """
    return grade_service.create_or_update_grade(db, current_user.id, grade_data)


@router.put(
    "/{grade_id}",
    response_model=GradeResponse,
    summary="Update an existing grade",
)
async def update_grade(
    grade_id: int,
    grade_data: GradeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing grade by its ID.

    Only the authenticated student's grades can be updated (ownership check).
    validation_status is recalculated automatically after update.

    Returns 404 if grade not found for this user.
    """
    return grade_service.update_grade(db, grade_id, current_user.id, grade_data)
