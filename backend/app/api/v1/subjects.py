"""
Subject management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
)

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subject.
    
    - **name**: Subject name (1-100 characters)
    - **priority**: Priority level (1-5 scale)
    - **difficulty**: Difficulty level (1-5 scale)
    - **target_weekly_hours**: Target weekly study hours (0.5-168 range)
    - **exam_date**: Optional exam date (must be future date)
    
    Maximum 100 subjects per user.
    """
    # Check maximum subjects limit
    subject_count = db.query(Subject).filter(Subject.user_id == current_user.id).count()
    if subject_count >= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum limit of 100 subjects reached"
        )
    
    # Create new subject
    new_subject = Subject(
        user_id=current_user.id,
        name=subject_data.name,
        priority=subject_data.priority,
        difficulty=subject_data.difficulty,
        target_weekly_hours=subject_data.target_weekly_hours,
        exam_date=subject_data.exam_date,
    )
    
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    
    return new_subject


@router.get("", response_model=SubjectListResponse)
async def list_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all subjects for the current user.
    
    Returns list of subjects ordered by priority (descending) and name.
    """
    subjects = db.query(Subject).filter(
        Subject.user_id == current_user.id
    ).order_by(
        Subject.priority.desc(),
        Subject.name
    ).all()
    
    return {
        "subjects": subjects,
        "total": len(subjects)
    }


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific subject by ID.
    
    Returns 404 if subject not found or doesn't belong to current user.
    """
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a subject.
    
    All fields are optional. Only provided fields will be updated.
    Returns 404 if subject not found or doesn't belong to current user.
    """
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Update only provided fields
    update_data = subject_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)
    
    db.commit()
    db.refresh(subject)
    
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_200_OK)
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a subject.
    
    This will also delete all associated study sessions (cascade delete).
    Returns 404 if subject not found or doesn't belong to current user.
    """
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db.delete(subject)
    db.commit()
    
    return {"message": "Subject deleted successfully"}
