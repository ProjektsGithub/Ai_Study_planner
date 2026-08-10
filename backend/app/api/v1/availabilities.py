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
from app.models.student_profile import StudentProfile
from app.models.class_schedule import ClassSchedule
from app.models.study_program import StudyProgram
from app.models.semester import Semester
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


@router.get("/academic-schedule")
async def get_academic_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detected university class schedule for current student based on profile preferences.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    
    if not profile or not profile.filiere_id:
        first_prog = db.query(StudyProgram).filter(StudyProgram.is_deleted == False).first()
        if first_prog:
            try:
                if not profile:
                    profile = StudentProfile(user_id=current_user.id, filiere_id=first_prog.id, current_semester=1)
                    db.add(profile)
                else:
                    profile.filiere_id = first_prog.id
                    if not profile.current_semester:
                        profile.current_semester = 1
                db.commit()
                db.refresh(profile)
            except Exception:
                db.rollback()
                profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not profile or not profile.filiere_id:
            return {
                "has_preferences": False,
                "program_name": None,
                "total_class_hours": 0,
                "academic_schedule": []
            }
    
    # Query program name & resolve all program IDs with same name
    program = db.query(StudyProgram).filter(StudyProgram.id == profile.filiere_id).first()
    program_name = program.name if program else "University Program"
    
    matching_prog_ids = [
        p.id for p in db.query(StudyProgram.id).filter(
            StudyProgram.name == program_name,
            StudyProgram.is_deleted == False
        ).all()
    ] if program else [profile.filiere_id]

    base_query = db.query(ClassSchedule).filter(
        ClassSchedule.study_program_id.in_(matching_prog_ids),
        ClassSchedule.is_deleted == False
    )
    query = base_query
    if profile.cursus_id:
        query = query.filter((ClassSchedule.academic_track_id == profile.cursus_id) | (ClassSchedule.academic_track_id == None))
    if profile.current_semester:
        sem_ids = [
            s.id for s in db.query(Semester.id).filter(
                Semester.semester_number == profile.current_semester,
                Semester.is_deleted == False
            ).all()
        ]
        if sem_ids:
            query = query.filter((ClassSchedule.semester_id.in_(sem_ids)) | (ClassSchedule.semester_id == None))
        
    schedules = query.all()
    if not schedules and not profile.cursus_id:
        schedules = base_query.all()
    
    # Calculate total class hours per week
    total_minutes = 0
    formatted_schedules = []
    for item in schedules:
        sh, sm = item.start_time.hour, item.start_time.minute
        eh, em = item.end_time.hour, item.end_time.minute
        dur = (eh * 60 + em) - (sh * 60 + sm)
        total_minutes += max(dur, 0)
        formatted_schedules.append({
            "id": item.id,
            "course_name": item.course_name,
            "course_code": item.course_code,
            "day_of_week": item.day_of_week,
            "start_time": item.start_time.strftime("%H:%M"),
            "end_time": item.end_time.strftime("%H:%M"),
            "session_type": item.session_type,
            "room_location": item.room_location,
            "is_mandatory": item.is_mandatory
        })
        
    return {
        "has_preferences": True,
        "program_name": program_name,
        "total_class_hours": round(total_minutes / 60.0, 1),
        "academic_schedule": formatted_schedules
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

