"""
Admin Class Schedules (Emplois du temps universitaires) CRUD API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.class_schedule import ClassSchedule
from app.schemas.class_schedule import (
    ClassScheduleCreate,
    ClassScheduleUpdate,
    ClassScheduleResponse,
    ClassScheduleListResponse,
)

router = APIRouter(prefix="/class-schedules", tags=["Class Schedules"])


@router.get("", response_model=ClassScheduleListResponse)
def list_class_schedules(
    study_program_id: Optional[int] = Query(None, description="Filter by study program (filière)"),
    academic_track_id: Optional[int] = Query(None, description="Filter by academic track (cursus)"),
    semester_id: Optional[int] = Query(None, description="Filter by semester"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all class schedules (admin / student readable)."""
    query = db.query(ClassSchedule).filter(ClassSchedule.is_deleted == False)

    if study_program_id:
        query = query.filter(ClassSchedule.study_program_id == study_program_id)
    if academic_track_id:
        query = query.filter(ClassSchedule.academic_track_id == academic_track_id)
    if semester_id:
        query = query.filter(ClassSchedule.semester_id == semester_id)

    items = query.all()
    return {"items": items, "total": len(items)}


@router.post("", response_model=ClassScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_class_schedule(
    data: ClassScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new university class schedule entry."""
    item = ClassSchedule(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{id}", response_model=ClassScheduleResponse)
def get_class_schedule(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific class schedule entry."""
    item = db.query(ClassSchedule).filter(ClassSchedule.id == id, ClassSchedule.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule entry not found")
    return item


@router.put("/{id}", response_model=ClassScheduleResponse)
def update_class_schedule(
    id: int,
    data: ClassScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update class schedule entry."""
    item = db.query(ClassSchedule).filter(ClassSchedule.id == id, ClassSchedule.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule entry not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_class_schedule(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete class schedule entry."""
    item = db.query(ClassSchedule).filter(ClassSchedule.id == id, ClassSchedule.is_deleted == False).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule entry not found")

    item.is_deleted = True
    db.commit()
    return {"message": "Class schedule deleted successfully"}
