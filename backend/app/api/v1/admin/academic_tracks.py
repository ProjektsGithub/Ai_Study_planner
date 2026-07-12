"""
Academic Track Management API Endpoints

Provides REST API endpoints for managing academic tracks (Cursus) including:
- Creating, reading, updating, and deleting academic tracks
- Filtering tracks by study program and level
- ECTS requirement validation
- Linking tracks to study programs
- RBAC middleware applied to all endpoints
- Audit logging for all operations

Requirements: 3.1-3.7
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import (
    require_role, 
    check_university_access, 
    get_accessible_universities,
    ROLE_SUPER_ADMIN, 
    ROLE_UNIVERSITY_ADMIN, 
    ROLE_PROGRAM_COORDINATOR
)
from app.models.user import User
from app.schemas.admin import (
    AcademicTrackCreate,
    AcademicTrackUpdate,
    AcademicTrackResponse,
    AcademicTrackListResponse,
    AcademicTrackDependentCountsResponse
)
from app.services.academic_track_service import AcademicTrackService
from app.services.audit_service import AuditService


router = APIRouter()


@router.post(
    "",
    response_model=AcademicTrackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new academic track",
    description="Create a new academic track for Bachelor, Master, or Doctorate level. Requires Super Admin role."
)
async def create_track(
    track_data: AcademicTrackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new academic track.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7
    
    - **study_program_id**: ID of the study program (required, must exist)
    - **name**: Track name in English (required, 1-255 characters)
    - **name_de**: Track name in German (optional, primary language)
    - **level**: Academic level: bachelor, master, or doctorate (required)
    - **description**: Track description in English (optional)
    - **description_de**: Track description in German (optional)
    - **total_ects_required**: Total ECTS for graduation (required, must be positive integer)
    - **graduation_conditions**: Graduation conditions in English (optional)
    - **graduation_conditions_de**: Graduation conditions in German (optional)
    
    Returns:
        The created academic track with all fields including ID and timestamps
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If study program not found
        400: If ECTS validation fails
    """
    # Apply RBAC - only Super Admin can create tracks
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can create academic tracks"
        )
    
    # Create track using service
    service = AcademicTrackService(db)
    try:
        track = await service.create_track(track_data.model_dump())
        
        # Log creation in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="academic_track",
            entity_id=track.id,
            data=track_data.model_dump(),
            user_id=current_user.id
        )
        
        return track
        
    except ValueError as e:
        # Determine appropriate status code based on error message
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.get(
    "",
    response_model=AcademicTrackListResponse,
    summary="List all academic tracks",
    description="Get paginated list of academic tracks with optional search and filters. Applies role-based filtering."
)
async def list_tracks(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by name or description"),
    study_program_id: Optional[int] = Query(None, description="Filter by study program ID"),
    level: Optional[str] = Query(None, description="Filter by level: bachelor, master, or doctorate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of academic tracks with optional filters.
    
    Requirements: 3.1-3.7
    
    Filters are applied based on user role:
    - **Super Admin**: Can see all tracks
    - **University Admin**: Can see tracks linked to their assigned universities
    - **Program Coordinator**: Can see tracks for their assigned programs
    
    Query Parameters:
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    - **search**: Search in name and description fields
    - **study_program_id**: Filter by study program ID
    - **level**: Filter by academic level (bachelor, master, doctorate)
    
    Returns:
        List of academic tracks with total count
    """
    # Apply RBAC - all admin roles can list tracks
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if study_program_id:
        filters["study_program_id"] = study_program_id
    if level:
        # Validate level value
        allowed_levels = ["bachelor", "master", "doctorate"]
        if level not in allowed_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level. Must be one of: {', '.join(allowed_levels)}"
            )
        filters["level"] = level
    
    # Get tracks using service
    service = AcademicTrackService(db)
    tracks, total = await service.get_tracks(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return {
        "tracks": tracks,
        "total": total
    }


@router.get(
    "/{track_id}",
    response_model=AcademicTrackResponse,
    summary="Get academic track details",
    description="Get detailed information about a specific academic track."
)
async def get_track(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific academic track.
    
    Requirements: 3.1-3.7
    
    Path Parameters:
    - **track_id**: ID of the academic track to retrieve
    
    Returns:
        Academic track details
        
    Raises:
        403: If user doesn't have access to view tracks
        404: If track not found
    """
    # Apply RBAC - all admin roles can view tracks
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get track using service
    service = AcademicTrackService(db)
    track = await service.get_track_by_id(track_id)
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {track_id} not found"
        )
    
    return track


@router.put(
    "/{track_id}",
    response_model=AcademicTrackResponse,
    summary="Update academic track",
    description="Update academic track information. Only provided fields will be updated."
)
async def update_track(
    track_id: int,
    track_data: AcademicTrackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update academic track information.
    
    Requirements: 3.5, 3.6
    
    Path Parameters:
    - **track_id**: ID of the academic track to update
    
    Body:
    - Only provided fields will be updated
    - All fields are optional in the update request
    
    Returns:
        Updated academic track details
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If track not found
        400: If validation fails (e.g., ECTS requirements)
    """
    # Apply RBAC - only Super Admin can update tracks
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can update academic tracks"
        )
    
    # Get before state for audit log
    service = AcademicTrackService(db)
    before_track = await service.get_track_by_id(track_id)
    
    if not before_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {track_id} not found"
        )
    
    # Convert to dict for audit log
    before_data = {
        "study_program_id": before_track.study_program_id,
        "name": before_track.name,
        "name_de": before_track.name_de,
        "level": before_track.level.value if hasattr(before_track.level, 'value') else before_track.level,
        "description": before_track.description,
        "description_de": before_track.description_de,
        "total_ects_required": before_track.total_ects_required,
        "graduation_conditions": before_track.graduation_conditions,
        "graduation_conditions_de": before_track.graduation_conditions_de
    }
    
    # Update track using service
    try:
        # Only include fields that were actually provided
        update_data = track_data.model_dump(exclude_unset=True)
        track = await service.update_track(track_id, update_data)
        
        # Log update in audit log
        after_data = {
            "study_program_id": track.study_program_id,
            "name": track.name,
            "name_de": track.name_de,
            "level": track.level.value if hasattr(track.level, 'value') else track.level,
            "description": track.description,
            "description_de": track.description_de,
            "total_ects_required": track.total_ects_required,
            "graduation_conditions": track.graduation_conditions,
            "graduation_conditions_de": track.graduation_conditions_de
        }
        
        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="academic_track",
            entity_id=track_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id
        )
        
        return track
        
    except ValueError as e:
        # Determine appropriate status code based on error message
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.delete(
    "/{track_id}",
    summary="Delete academic track",
    description="Soft delete an academic track. Returns counts of dependent entities that will be affected."
)
async def delete_track(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete an academic track.
    
    Requirements: 3.1-3.7
    
    This operation:
    - Marks the track as deleted (soft delete)
    - Also marks associated semesters as deleted
    - Returns counts of all dependent entities
    
    Path Parameters:
    - **track_id**: ID of the academic track to delete
    
    Returns:
        Success message and counts of dependent entities
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If track not found
    """
    # Apply RBAC - only Super Admin can delete tracks
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete academic tracks"
        )
    
    # Get before state for audit log
    service = AcademicTrackService(db)
    track = await service.get_track_by_id(track_id)
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {track_id} not found"
        )
    
    before_data = {
        "name": track.name,
        "name_de": track.name_de,
        "level": track.level.value if hasattr(track.level, 'value') else track.level,
        "study_program_id": track.study_program_id
    }
    
    # Delete track using service
    try:
        result = await service.delete_track(track_id)
        
        # Log deletion in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="academic_track",
            entity_id=track_id,
            data=before_data,
            user_id=current_user.id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{track_id}/dependents",
    response_model=AcademicTrackDependentCountsResponse,
    summary="Get dependent entity counts",
    description="Get counts of all entities that depend on this academic track (semesters, teaching units, courses)."
)
async def get_dependent_counts(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of entities dependent on this academic track.
    
    Requirements: 3.1-3.7
    
    Useful for validation before deletion to understand the impact.
    
    Path Parameters:
    - **track_id**: ID of the academic track
    
    Returns:
        Dictionary with counts:
        - semesters_count: Number of semesters
        - courses_count: Number of courses (through semesters)
        
    Raises:
        403: If user doesn't have access
        404: If track not found
    """
    # Apply RBAC - all admin roles can view dependent counts
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if track exists
    service = AcademicTrackService(db)
    track = await service.get_track_by_id(track_id)
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {track_id} not found"
        )
    
    # Get dependent counts
    counts = await service.get_dependent_counts(track_id)
    
    return {
        "semesters_count": counts.get("semesters", 0),
        "courses_count": counts.get("courses", 0)
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _check_role(user: User, allowed_roles: List[str], db: Session) -> bool:
    """
    Check if user has one of the allowed roles.
    
    Args:
        user: Current user
        allowed_roles: List of role names
        db: Database session
        
    Returns:
        True if user has any of the allowed roles, False otherwise
    """
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole
    
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.name.in_(allowed_roles),
        AdminRole.is_active == True
    ).all()
    
    return len(user_roles) > 0
