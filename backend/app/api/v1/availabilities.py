"""
Availability management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.availability import Availability
from app.models.study_plan import StudyPlan
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    AvailabilityListResponse,
)

router = APIRouter(prefix="/availabilities", tags=["Availabilities"])


def mark_future_plans_outdated(user_id: int, db: Session):
    """
    Mark all future study plans as outdated when availabilities change.
    This ensures users regenerate plans with updated availability.
    """
    db.query(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.status == "generated"
    ).update({"status": "outdated"})
    db.commit()


@router.post("", response_model=AvailabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_availability(
    availability_data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new availability time slot.
    
    - **day_of_week**: Day of the week (Monday-Sunday)
    - **start_time**: Start time in HH:MM format (24-hour)
    - **end_time**: End time in HH:MM format (24-hour, must be after start_time)
    
    Note: Overlapping availabilities are allowed for the same day.
    Creating an availability will mark future study plans as outdated.
    """
    # Create new availability
    new_availability = Availability(
        user_id=current_user.id,
        day_of_week=availability_data.day_of_week.value,
        start_time=availability_data.start_time,
        end_time=availability_data.end_time,
    )
    
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    
    # Mark future plans as outdated
    mark_future_plans_outdated(current_user.id, db)
    
    return new_availability


@router.get("", response_model=AvailabilityListResponse)
async def list_availabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all availabilities for the current user.
    
    Returns list of availabilities ordered by day of week and start time.
    """
    # Define day order for sorting
    day_order = {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 7
    }
    
    availabilities = db.query(Availability).filter(
        Availability.user_id == current_user.id
    ).all()
    
    # Sort by day of week and start time
    availabilities.sort(key=lambda x: (day_order.get(x.day_of_week, 8), x.start_time))
    
    return {
        "availabilities": availabilities,
        "total": len(availabilities)
    }


@router.get("/{availability_id}", response_model=AvailabilityResponse)
async def get_availability(
    availability_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific availability by ID.
    
    Returns 404 if availability not found or doesn't belong to current user.
    """
    availability = db.query(Availability).filter(
        Availability.id == availability_id,
        Availability.user_id == current_user.id
    ).first()
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    return availability


@router.put("/{availability_id}", response_model=AvailabilityResponse)
async def update_availability(
    availability_id: int,
    availability_data: AvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an availability.
    
    All fields are optional. Only provided fields will be updated.
    Returns 404 if availability not found or doesn't belong to current user.
    Updating an availability will mark future study plans as outdated.
    """
    availability = db.query(Availability).filter(
        Availability.id == availability_id,
        Availability.user_id == current_user.id
    ).first()
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    # Update only provided fields
    update_data = availability_data.model_dump(exclude_unset=True)
    
    # Convert enum to string if day_of_week is provided
    if 'day_of_week' in update_data and update_data['day_of_week'] is not None:
        update_data['day_of_week'] = update_data['day_of_week'].value
    
    # If updating times, validate the range
    start_time = update_data.get('start_time', availability.start_time)
    end_time = update_data.get('end_time', availability.end_time)
    
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    for field, value in update_data.items():
        setattr(availability, field, value)
    
    db.commit()
    db.refresh(availability)
    
    # Mark future plans as outdated
    mark_future_plans_outdated(current_user.id, db)
    
    return availability


@router.delete("/{availability_id}", status_code=status.HTTP_200_OK)
async def delete_availability(
    availability_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an availability.
    
    Returns 404 if availability not found or doesn't belong to current user.
    Deleting an availability will mark future study plans as outdated.
    """
    availability = db.query(Availability).filter(
        Availability.id == availability_id,
        Availability.user_id == current_user.id
    ).first()
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    db.delete(availability)
    db.commit()
    
    # Mark future plans as outdated
    mark_future_plans_outdated(current_user.id, db)
    
    return {"message": "Availability deleted successfully"}
