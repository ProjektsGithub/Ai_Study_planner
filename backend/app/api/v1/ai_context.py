"""
AI Context API Endpoints

GET  /api/v1/ai-context               — complete AI context JSON for current user
POST /api/v1/ai-context               — same but with request options

Requirements: 16.12, 16.13–16.17, 19.4, 13.14
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.ai_context import AIContextResponse, AIContextRequest
from app.services.ai_context_service import ai_context_service

router = APIRouter(prefix="/ai-context", tags=["AI Context"])


@router.get(
    "",
    response_model=AIContextResponse,
    summary="Get full AI context for the authenticated student",
)
async def get_ai_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build and return the complete AI context JSON payload for the student.

    This aggregates data from all academic services:
    - **student_profile**: university, filière, cursus, semester, academic_year
    - **academic_progress**: ECTS obtained/required/remaining/percentage
    - **failed_courses**: failed courses with attempt count and blocker status
    - **course_priorities**: priority scores, recommended hours, success probability
    - **availability_slots**: study availability windows
    - **constraints**: student constraints (job, internship, etc.)
    - **upcoming_exams**: future exams with countdown

    All floats are rounded to 2 decimal places.
    All timestamps are ISO 8601.

    This endpoint is called by the AI study plan generator before generation.
    """
    return ai_context_service.build_context(db, current_user.id)


@router.post(
    "",
    response_model=AIContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI context with custom options",
)
async def get_ai_context_with_options(
    request: AIContextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build the AI context with optional filtering.

    Request body options:
    - **include_risk_details**: include factor breakdown in risk scores (default: true)
    - **include_priority_factors**: include factor breakdown in priorities (default: true)
    """
    return ai_context_service.build_context(db, current_user.id, request)
