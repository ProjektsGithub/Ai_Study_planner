"""
Plan Optimizer API Endpoints

POST /api/v1/study-plans/regenerate   — trigger plan regeneration
POST /api/v1/study-plans/complete     — mark session complete and recalculate

Requirements: 16.12, 16.13, 16.14, 19.6, 14.7
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.plan_optimizer_service import plan_optimizer_service

router = APIRouter(prefix="/study-plans", tags=["Plan Optimizer"])


class RegenerateRequest(BaseModel):
    """Request body for plan regeneration trigger"""
    modification_type: str = Field(
        default="manual_edit",
        description="What triggered the regeneration: grade_update | exam_update | profile_update | session_complete | session_delete | manual_edit",
    )
    session_id: Optional[int] = Field(
        None,
        description="Optional study session ID that was modified",
    )
    reason: Optional[str] = Field(
        None,
        description="Human-readable description of the trigger",
    )


class CompleteSessionRequest(BaseModel):
    """Request body for marking a session complete"""
    session_id: int = Field(..., description="Study session ID to mark as complete")


@router.post(
    "/regenerate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger study plan regeneration",
)
async def trigger_regeneration(
    request: RegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger an asynchronous study plan regeneration.

    The regeneration runs in the background — the response is immediate
    (< 1 second). Regeneration completes within 5 seconds for typical profiles.

    A notification is sent to the student when regeneration is queued.

    **modification_type** values:
    - `grade_update` — a grade was created or updated
    - `exam_update` — an exam was created, updated, or deleted
    - `profile_update` — academic profile (cursus/semester) changed
    - `session_complete` — a study session was marked complete
    - `session_delete` — a study session was deleted
    - `manual_edit` — user manually edited a session
    """
    return plan_optimizer_service.trigger_regeneration(
        db=db,
        user_id=current_user.id,
        modification_type=request.modification_type,
        session_id=request.session_id,
        reason=request.reason,
    )


@router.post(
    "/complete-session",
    status_code=status.HTTP_200_OK,
    summary="Mark a study session as complete and recalculate",
)
async def complete_session(
    request: CompleteSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a study session as complete and trigger plan recalculation.

    This updates the session's completed status and triggers a plan
    regeneration to reflect the progress change.

    Returns 404 if session not found for this user.
    """
    return plan_optimizer_service.update_progress_and_recalculate(
        db=db,
        user_id=current_user.id,
        session_id=request.session_id,
    )
