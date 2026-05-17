"""
Profile management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.dependencies import get_db, get_current_user
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.schemas.auth import MessageResponse
from app.models.user import User
from app.models.student_profile import StudentProfile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update student profile.
    
    If profile exists, updates it. Otherwise, creates a new one.
    
    - **cursus**: Academic program/cursus (1-100 characters)
    - **academic_level**: Current academic level (1-50 characters)
    - **weekly_study_goal**: Weekly study goal in hours (1-168)
    - **preferences**: Optional JSON preferences
    """
    # Check if profile already exists
    existing_profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        # Update existing profile
        existing_profile.cursus = profile_data.cursus
        existing_profile.academic_level = profile_data.academic_level
        existing_profile.weekly_study_goal = profile_data.weekly_study_goal
        existing_profile.preferences = profile_data.preferences
        existing_profile.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(existing_profile)
        
        return existing_profile
    else:
        # Create new profile
        new_profile = StudentProfile(
            user_id=current_user.id,
            cursus=profile_data.cursus,
            academic_level=profile_data.academic_level,
            weekly_study_goal=profile_data.weekly_study_goal,
            preferences=profile_data.preferences,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        return new_profile


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's student profile.
    
    Returns the complete profile data including preferences.
    """
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    
    return profile


@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update student profile.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    
    - **cursus**: Academic program/cursus (1-100 characters)
    - **academic_level**: Current academic level (1-50 characters)
    - **weekly_study_goal**: Weekly study goal in hours (1-168)
    - **preferences**: Optional JSON preferences
    """
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create a profile first."
        )
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("", response_model=MessageResponse)
async def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete student profile.
    
    This will remove the profile but keep the user account.
    """
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    db.delete(profile)
    db.commit()
    
    return {"message": "Profile deleted successfully"}
