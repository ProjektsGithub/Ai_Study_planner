"""
Study Plan API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.study_plan import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    StudyPlanResponse,
    StudyPlanHistoryResponse
)
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse
)
from app.services.study_plan_service import StudyPlanService
from app.services.session_edit_service import SessionEditService

router = APIRouter(prefix="/study-plans", tags=["study-plans"])


@router.post("/generate", response_model=GeneratePlanResponse)
def generate_study_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new study plan for the specified week.
    
    - **week_start**: Start date of the week (must be Monday)
    - **force_regenerate**: Skip cache and force new generation
    
    Returns the generated plan with sessions, or error details if generation fails.
    """
    service = StudyPlanService(db)
    
    success, result = service.generate_plan(
        user_id=current_user.id,
        week_start=request.week_start,
        force_regenerate=request.force_regenerate
    )
    
    if not success:
        # Return error response with appropriate status code
        error_type = result.get("error", "unknown_error")
        
        if error_type in ["user_not_found", "profile_not_found"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Resource not found")
            )
        elif error_type in ["no_subjects", "no_availabilities", "no_valid_slots"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Invalid request")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Internal server error")
            )
    
    return GeneratePlanResponse(**result)


@router.get("/current", response_model=Optional[StudyPlanResponse])
def get_current_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current active study plan for the authenticated user.
    
    Returns the most recent plan with status 'generated', or null if no active plan exists.
    """
    service = StudyPlanService(db)
    
    plan = service.get_current_plan(current_user.id)
    
    if not plan:
        return None
    
    return StudyPlanResponse(**plan)


@router.get("/history", response_model=StudyPlanHistoryResponse)
def get_plan_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated history of all study plans for the authenticated user.
    
    - **page**: Page number (default: 1)
    
    Returns 20 plans per page, ordered by creation date descending.
    Plans older than 90 days are automatically deleted by background job.
    """
    service = StudyPlanService(db)
    
    result = service.get_plan_history(
        user_id=current_user.id,
        page=page,
        page_size=20
    )
    
    return StudyPlanHistoryResponse(**result)


@router.get("/{plan_id}", response_model=StudyPlanResponse)
def get_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a study plan by its UUID.
    
    - **plan_id**: Plan UUID
    
    Returns the plan with all sessions.
    """
    service = StudyPlanService(db)
    
    plan = service.get_plan_by_id(plan_id, current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study plan not found"
        )
    
    return StudyPlanResponse(**plan)


@router.post("/{plan_id}/restore", response_model=GeneratePlanResponse)
def restore_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore a previous study plan by creating a new active plan with the same sessions.
    
    - **plan_id**: Plan UUID to restore
    
    Creates a new plan with status 'generated' and marks the previous active plan as 'superseded'.
    The restored plan gets a new UUID and creation timestamp.
    """
    service = StudyPlanService(db)
    
    success, result = service.restore_plan(
        plan_id=plan_id,
        user_id=current_user.id
    )
    
    if not success:
        error_type = result.get("error", "unknown_error")
        
        if error_type == "plan_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Plan not found")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Internal server error")
            )
    
    return GeneratePlanResponse(**result)



# Session editing endpoints

@router.post("/{plan_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def add_session(
    plan_id: int,
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new session to a study plan.
    
    - **plan_id**: Study plan ID
    - **subject_id**: Subject ID
    - **day**: Day of week (Monday-Sunday)
    - **start_time**: Start time (HH:MM:SS)
    - **end_time**: End time (HH:MM:SS)
    - **task_type**: Task type (lecture_review, exercise_practice, exam_preparation, project_work, reading)
    - **notes**: Optional notes
    
    Validates:
    - Subject belongs to user
    - Time format and logic
    - Session falls within availability
    - Doesn't violate constraints
    - Doesn't overlap with other sessions
    - Maximum 50 sessions per plan
    """
    service = SessionEditService(db)
    
    session_data = request.model_dump()
    
    success, result = service.add_session(
        plan_id=plan_id,
        user_id=current_user.id,
        session_data=session_data
    )
    
    if not success:
        error_type = result.get("error", "unknown_error")
        
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Resource not found")
            )
        elif error_type in ["validation_error", "session_limit_exceeded"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Invalid request")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Internal server error")
            )
    
    return SessionResponse(**result["session"])


@router.put("/{plan_id}/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    plan_id: int,
    session_id: int,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing session.
    
    - **plan_id**: Study plan ID
    - **session_id**: Session ID
    
    All fields are optional. Only provided fields will be updated.
    
    Validates:
    - Subject belongs to user (if provided)
    - Time format and logic (if provided)
    - Session falls within availability (if time/day changed)
    - Doesn't violate constraints (if time/day changed)
    - Doesn't overlap with other sessions (if time/day changed)
    """
    service = SessionEditService(db)
    
    # Only include non-None fields
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    success, result = service.update_session(
        plan_id=plan_id,
        session_id=session_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    if not success:
        error_type = result.get("error", "unknown_error")
        
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Resource not found")
            )
        elif error_type == "validation_error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Invalid request")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Internal server error")
            )
    
    return SessionResponse(**result["session"])


@router.delete("/{plan_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    plan_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a session from a study plan.
    
    - **plan_id**: Study plan ID
    - **session_id**: Session ID
    
    Marks the plan as edited.
    """
    service = SessionEditService(db)
    
    success, result = service.delete_session(
        plan_id=plan_id,
        session_id=session_id,
        user_id=current_user.id
    )
    
    if not success:
        error_type = result.get("error", "unknown_error")
        
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Resource not found")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Internal server error")
            )
    
    return None
