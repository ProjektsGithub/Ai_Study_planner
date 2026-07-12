"""
Semester Configuration API Endpoints

Provides REST API endpoints for managing semesters including:
- Creating, reading, updating, and deleting semesters
- Filtering semesters by academic track and semester number
- Semester structure validation (S1-S6 for Bachelor, S1-S4 for Master)
- Linking semesters to academic tracks
- RBAC middleware applied to all endpoints
- Audit logging for all operations

Requirements: 4.1-4.7
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
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse,
    SemesterListResponse,
    SemesterDependentCountsResponse
)
from app.services.semester_service import SemesterService
from app.services.audit_service import AuditService


router = APIRouter()


@router.post(
    "",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new semester",
    description="Create a new semester for an academic track. Validates S1-S6 for Bachelor, S1-S4 for Master. Requires Super Admin role."
)
async def create_semester(
    semester_data: SemesterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new semester.
    
    Requirements: 4.1, 4.2, 4.3, 4.5, 4.6
    
    - **academic_track_id**: ID of the academic track (required, must exist)
    - **name**: Semester name (required, e.g., "S1", "S2")
    - **name_de**: Semester name in German (optional)
    - **semester_number**: Semester number (required, 1-6 for Bachelor, 1-4 for Master)
    - **description**: Semester description in English (optional)
    - **description_de**: Semester description in German (optional)
    - **ects_required**: ECTS requirements for this semester (optional, non-negative)
    
    Returns:
        The created semester with all fields including ID and timestamps
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If academic track not found
        400: If validation fails (duplicate semester, invalid structure)
    """
    # Apply RBAC - only Super Admin can create semesters
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can create semesters"
        )
    
    # Create semester using service
    service = SemesterService(db)
    try:
        semester = await service.create_semester(semester_data.model_dump())
        
        # Log creation in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="semester",
            entity_id=semester.id,
            data=semester_data.model_dump(),
            user_id=current_user.id
        )
        
        return semester
        
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
    response_model=SemesterListResponse,
    summary="List all semesters",
    description="Get paginated list of semesters with optional search and filters. Applies role-based filtering."
)
async def list_semesters(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by name or description"),
    academic_track_id: Optional[int] = Query(None, description="Filter by academic track ID"),
    semester_number: Optional[int] = Query(None, description="Filter by semester number"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of semesters with optional filters.
    
    Requirements: 4.1-4.7
    
    Filters are applied based on user role:
    - **Super Admin**: Can see all semesters
    - **University Admin**: Can see semesters linked to their assigned universities
    - **Program Coordinator**: Can see semesters for their assigned programs
    
    Query Parameters:
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    - **search**: Search in name and description fields
    - **academic_track_id**: Filter by academic track ID
    - **semester_number**: Filter by semester number
    
    Returns:
        List of semesters with total count
    """
    # Apply RBAC - all admin roles can list semesters
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if academic_track_id:
        filters["academic_track_id"] = academic_track_id
    if semester_number:
        filters["semester_number"] = semester_number
    
    # Get semesters using service
    service = SemesterService(db)
    semesters, total = await service.get_semesters(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return {
        "semesters": semesters,
        "total": total
    }


@router.get(
    "/{semester_id}",
    response_model=SemesterResponse,
    summary="Get semester details",
    description="Get detailed information about a specific semester."
)
async def get_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific semester.
    
    Requirements: 4.1-4.7
    
    Path Parameters:
    - **semester_id**: ID of the semester to retrieve
    
    Returns:
        Semester details
        
    Raises:
        403: If user doesn't have access to view semesters
        404: If semester not found
    """
    # Apply RBAC - all admin roles can view semesters
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get semester using service
    service = SemesterService(db)
    semester = await service.get_semester_by_id(semester_id)
    
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found"
        )
    
    return semester


@router.put(
    "/{semester_id}",
    response_model=SemesterResponse,
    summary="Update semester",
    description="Update semester information. Only provided fields will be updated."
)
async def update_semester(
    semester_id: int,
    semester_data: SemesterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update semester information.
    
    Requirements: 4.5
    
    Path Parameters:
    - **semester_id**: ID of the semester to update
    
    Body:
    - Only provided fields will be updated
    - All fields are optional in the update request
    
    Returns:
        Updated semester details
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If semester not found
        400: If validation fails (duplicate semester, invalid structure)
    """
    # Apply RBAC - only Super Admin can update semesters
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can update semesters"
        )
    
    # Get before state for audit log
    service = SemesterService(db)
    before_semester = await service.get_semester_by_id(semester_id)
    
    if not before_semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found"
        )
    
    # Convert to dict for audit log
    before_data = {
        "academic_track_id": before_semester.academic_track_id,
        "name": before_semester.name,
        "name_de": before_semester.name_de,
        "semester_number": before_semester.semester_number,
        "description": before_semester.description,
        "description_de": before_semester.description_de,
        "ects_required": before_semester.ects_required
    }
    
    # Update semester using service
    try:
        # Only include fields that were actually provided
        update_data = semester_data.model_dump(exclude_unset=True)
        semester = await service.update_semester(semester_id, update_data)
        
        # Log update in audit log
        after_data = {
            "academic_track_id": semester.academic_track_id,
            "name": semester.name,
            "name_de": semester.name_de,
            "semester_number": semester.semester_number,
            "description": semester.description,
            "description_de": semester.description_de,
            "ects_required": semester.ects_required
        }
        
        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="semester",
            entity_id=semester_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id
        )
        
        return semester
        
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
    "/{semester_id}",
    summary="Delete semester",
    description="Soft delete a semester. Prevents deletion if courses are assigned."
)
async def delete_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a semester.
    
    Requirements: 4.7
    
    This operation:
    - Marks the semester as deleted (soft delete)
    - Also marks associated teaching units as deleted
    - Prevents deletion if courses are assigned
    - Returns counts of all dependent entities
    
    Path Parameters:
    - **semester_id**: ID of the semester to delete
    
    Returns:
        Success message and counts of dependent entities
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If semester not found
        400: If semester has assigned courses
    """
    # Apply RBAC - only Super Admin can delete semesters
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete semesters"
        )
    
    # Get before state for audit log
    service = SemesterService(db)
    semester = await service.get_semester_by_id(semester_id)
    
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found"
        )
    
    before_data = {
        "name": semester.name,
        "name_de": semester.name_de,
        "semester_number": semester.semester_number,
        "academic_track_id": semester.academic_track_id
    }
    
    # Delete semester using service
    try:
        result = await service.delete_semester(semester_id)
        
        # Log deletion in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="semester",
            entity_id=semester_id,
            data=before_data,
            user_id=current_user.id
        )
        
        return result
        
    except ValueError as e:
        # Check if it's a validation error (courses assigned) or not found
        if "cannot delete" in str(e).lower() or "assigned courses" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


@router.get(
    "/{semester_id}/dependents",
    response_model=SemesterDependentCountsResponse,
    summary="Get dependent entity counts",
    description="Get counts of all entities that depend on this semester (teaching units, courses)."
)
async def get_dependent_counts(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of entities dependent on this semester.
    
    Requirements: 4.1-4.7
    
    Useful for validation before deletion to understand the impact.
    
    Path Parameters:
    - **semester_id**: ID of the semester
    
    Returns:
        Dictionary with counts:
        - teaching_units_count: Number of teaching units
        - courses_count: Number of courses
        
    Raises:
        403: If user doesn't have access
        404: If semester not found
    """
    # Apply RBAC - all admin roles can view dependent counts
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if semester exists
    service = SemesterService(db)
    semester = await service.get_semester_by_id(semester_id)
    
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester with ID {semester_id} not found"
        )
    
    # Get dependent counts
    counts = await service.get_dependent_counts(semester_id)
    
    return {
        "teaching_units_count": counts.get("teaching_units", 0),
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
