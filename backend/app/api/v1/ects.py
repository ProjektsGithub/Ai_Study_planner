"""
ECTS Progress API Endpoints

GET /api/v1/ects/progression           — ECTS obtained/required/remaining
GET /api/v1/ects/progression/breakdown — + per-semester breakdown
POST /api/v1/ects/progression/recalculate — force recalculation

Requirements: 16.3, 16.13–16.17, 19.1
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.ects_progress import ECTSProgressionResponse, ECTSProgressWithBreakdown
from app.schemas.auth import MessageResponse
from app.services.ects_service import ects_service

router = APIRouter(prefix="/ects", tags=["ECTS Progress"])


@router.get(
    "/progression",
    response_model=ECTSProgressionResponse,
    summary="Get ECTS progression",
)
async def get_ects_progression(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the student's ECTS progression:
    - **ects_obtained**: total credits from validated courses
    - **ects_required**: total credits for graduation
    - **ects_remaining**: credits still to earn
    - **progression_percentage**: (obtained / required) × 100, 2 decimal places
    """
    return ects_service.get_progression(db, current_user.id)


@router.get(
    "/progression/breakdown",
    response_model=ECTSProgressWithBreakdown,
    summary="Get ECTS progression with per-semester breakdown",
)
async def get_ects_progression_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return ECTS progression with a breakdown per semester.

    Each semester entry shows ects_obtained, ects_required, and progression_percentage.
    """
    return ects_service.get_full_progression(db, current_user.id)


@router.post(
    "/progression/recalculate",
    response_model=ECTSProgressionResponse,
    status_code=status.HTTP_200_OK,
    summary="Force ECTS progression recalculation",
)
async def recalculate_ects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force a fresh ECTS recalculation from the current validated grades.

    Useful after importing grades or if progression seems stale.
    """
    return ects_service.calculate_progression(db, current_user.id)
