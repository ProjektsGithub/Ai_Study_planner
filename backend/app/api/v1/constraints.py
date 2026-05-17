"""
Constraint management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.constraint import Constraint
from app.models.subject import Subject
from app.schemas.constraint import (
    ConstraintCreate,
    ConstraintUpdate,
    ConstraintResponse,
    ConstraintListResponse,
    ConstraintType,
)

router = APIRouter(prefix="/constraints", tags=["Constraints"])


def validate_subject_reference(subject_id: int, user_id: int, db: Session) -> bool:
    """Validate that subject exists and belongs to user"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    return subject is not None


@router.post("", response_model=ConstraintResponse, status_code=status.HTTP_201_CREATED)
async def create_constraint(
    constraint_data: ConstraintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new constraint.
    
    **Constraint Types:**
    
    1. **forbidden_slot**: Block specific time slots
       - Parameters: day_of_week, start_time, end_time
       - Example: {"day_of_week": "Monday", "start_time": "12:00:00", "end_time": "13:00:00"}
    
    2. **max_daily_hours**: Limit daily study hours
       - Parameters: max_hours (1-24)
       - Example: {"max_hours": 8}
    
    3. **required_break**: Enforce breaks after continuous study
       - Parameters: duration_minutes (5-120), after_minutes (30-240)
       - Example: {"duration_minutes": 15, "after_minutes": 90}
    
    4. **fixed_slot**: Reserve specific time for a subject
       - Parameters: day_of_week, start_time, end_time, subject_id
       - Example: {"day_of_week": "Wednesday", "start_time": "14:00:00", "end_time": "16:00:00", "subject_id": 1}
    
    Maximum 50 constraints per user.
    """
    # Check maximum constraints limit
    constraint_count = db.query(Constraint).filter(Constraint.user_id == current_user.id).count()
    if constraint_count >= 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum limit of 50 constraints reached"
        )
    
    # Validate subject reference for fixed_slot
    if constraint_data.constraint_type == ConstraintType.FIXED_SLOT:
        subject_id = constraint_data.parameters.get("subject_id")
        if not validate_subject_reference(subject_id, current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with id {subject_id} not found or doesn't belong to user"
            )
    
    # Create new constraint
    new_constraint = Constraint(
        user_id=current_user.id,
        constraint_type=constraint_data.constraint_type.value,
        parameters=constraint_data.parameters,
        active=constraint_data.active,
    )
    
    db.add(new_constraint)
    db.commit()
    db.refresh(new_constraint)
    
    return new_constraint


@router.get("", response_model=ConstraintListResponse)
async def list_constraints(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all constraints for the current user.
    
    - **active_only**: If True, return only active constraints
    
    Returns list of constraints ordered by creation date (newest first).
    """
    query = db.query(Constraint).filter(Constraint.user_id == current_user.id)
    
    if active_only:
        query = query.filter(Constraint.active == True)
    
    constraints = query.order_by(Constraint.created_at.desc()).all()
    
    active_count = sum(1 for c in constraints if c.active)
    inactive_count = len(constraints) - active_count
    
    return {
        "constraints": constraints,
        "total": len(constraints),
        "active_count": active_count,
        "inactive_count": inactive_count
    }


@router.get("/{constraint_id}", response_model=ConstraintResponse)
async def get_constraint(
    constraint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific constraint by ID.
    
    Returns 404 if constraint not found or doesn't belong to current user.
    """
    constraint = db.query(Constraint).filter(
        Constraint.id == constraint_id,
        Constraint.user_id == current_user.id
    ).first()
    
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constraint not found"
        )
    
    return constraint


@router.put("/{constraint_id}", response_model=ConstraintResponse)
async def update_constraint(
    constraint_id: int,
    constraint_data: ConstraintUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a constraint.
    
    All fields are optional. Only provided fields will be updated.
    Returns 404 if constraint not found or doesn't belong to current user.
    """
    constraint = db.query(Constraint).filter(
        Constraint.id == constraint_id,
        Constraint.user_id == current_user.id
    ).first()
    
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constraint not found"
        )
    
    # Update only provided fields
    update_data = constraint_data.model_dump(exclude_unset=True)
    
    # Convert enum to string if constraint_type is provided
    if 'constraint_type' in update_data and update_data['constraint_type'] is not None:
        update_data['constraint_type'] = update_data['constraint_type'].value
    
    # Validate subject reference for fixed_slot
    if 'constraint_type' in update_data or 'parameters' in update_data:
        final_type = update_data.get('constraint_type', constraint.constraint_type)
        final_params = update_data.get('parameters', constraint.parameters)
        
        if final_type == "fixed_slot":
            subject_id = final_params.get("subject_id")
            if not validate_subject_reference(subject_id, current_user.id, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject with id {subject_id} not found or doesn't belong to user"
                )
    
    for field, value in update_data.items():
        setattr(constraint, field, value)
    
    db.commit()
    db.refresh(constraint)
    
    return constraint


@router.patch("/{constraint_id}/toggle", response_model=ConstraintResponse)
async def toggle_constraint(
    constraint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle constraint active status (active <-> inactive).
    
    Returns 404 if constraint not found or doesn't belong to current user.
    """
    constraint = db.query(Constraint).filter(
        Constraint.id == constraint_id,
        Constraint.user_id == current_user.id
    ).first()
    
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constraint not found"
        )
    
    constraint.active = not constraint.active
    db.commit()
    db.refresh(constraint)
    
    return constraint


@router.delete("/{constraint_id}", status_code=status.HTTP_200_OK)
async def delete_constraint(
    constraint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a constraint.
    
    Returns 404 if constraint not found or doesn't belong to current user.
    """
    constraint = db.query(Constraint).filter(
        Constraint.id == constraint_id,
        Constraint.user_id == current_user.id
    ).first()
    
    if not constraint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constraint not found"
        )
    
    db.delete(constraint)
    db.commit()
    
    return {"message": "Constraint deleted successfully"}
