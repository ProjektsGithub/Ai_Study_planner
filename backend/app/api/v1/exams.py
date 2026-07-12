"""
Exam API Endpoints

GET    /api/v1/exams                  — upcoming exams sorted by date with countdown
GET    /api/v1/exams/all              — all exams including past
POST   /api/v1/exams                  — create exam
PUT    /api/v1/exams/{exam_id}        — update exam (ownership check)
DELETE /api/v1/exams/{exam_id}        — delete exam (ownership check)

Requirements: 16.7, 16.8, 16.13–16.17, 19.5, 20.3, 20.8
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamUpdate, ExamWithCountdown, ExamListResponse
from app.schemas.auth import MessageResponse
from app.services.exam_service import exam_service

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get(
    "",
    response_model=ExamListResponse,
    summary="Get upcoming exams with countdown",
)
async def get_upcoming_exams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all future exams for the authenticated student, sorted by date ascending.

    Each exam includes **days_until** countdown (positive = future).
    Past exams are excluded — use /exams/all to include them.
    """
    exams = exam_service.get_upcoming_exams(db, current_user.id)
    return ExamListResponse(exams=exams, total=len(exams))


@router.get(
    "/all",
    response_model=ExamListResponse,
    summary="Get all exams including past",
)
async def get_all_exams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all exams (past and future) for the authenticated student.

    **days_until** is negative for past exams.
    """
    exams = exam_service.get_all_exams(db, current_user.id)
    return ExamListResponse(exams=exams, total=len(exams))


@router.post(
    "",
    response_model=ExamWithCountdown,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exam",
)
async def create_exam(
    exam_data: ExamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new exam entry for the authenticated student.

    Validation:
    - **exam_date**: must be YYYY-MM-DD format
    - **weight**: must be between 0.0 and 1.0 (e.g. 0.6 = 60% of final grade)
    - **exam_type**: midterm | final | practical | oral | project

    Triggers study plan regeneration to account for new exam proximity.
    """
    exam = exam_service.create_exam(db, current_user.id, exam_data)
    return exam_service._to_countdown(exam)


@router.put(
    "/{exam_id}",
    response_model=ExamWithCountdown,
    summary="Update an exam",
)
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing exam by ID.

    Only the authenticated student's exams can be updated (ownership check).
    Returns 404 if exam not found for this user.
    """
    exam = exam_service.update_exam(db, exam_id, current_user.id, exam_data)
    return exam_service._to_countdown(exam)


@router.delete(
    "/{exam_id}",
    response_model=MessageResponse,
    summary="Delete an exam",
)
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an exam by ID.

    Only the authenticated student's exams can be deleted (ownership check).
    Returns 404 if exam not found for this user.
    """
    exam_service.delete_exam(db, exam_id, current_user.id)
    return {"message": "Exam deleted successfully"}
