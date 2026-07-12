"""
Teaching Unit Configuration API Endpoints

Provides REST API endpoints for managing teaching units (UE - Unité d'Enseignement) including:
- Creating, reading, updating, and deleting teaching units
- Filtering teaching units by semester and academic track
- Linking teaching units to semesters
- ECTS requirements validation
- RBAC middleware applied to all endpoints
- Audit logging for all operations

Requirements: 5.1-5.7
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
    TeachingUnitCreate,
    TeachingUnitUpdate,
    TeachingUnitResponse,
    TeachingUnitListResponse,
    TeachingUnitDependentCountsResponse
)
from app.services.teaching_unit_service import TeachingUnitService
from app.services.audit_service import AuditService


router = APIRouter()


@router.post(
    "",
    response_model=TeachingUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new teaching unit",
    description="Create a new teaching unit for a semester. Validates ECTS requirements. Requires Super Admin role."
)
async def create_teaching_unit(
    teaching_unit_data: TeachingUnitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new teaching unit.
    
    Requirements: 5.1, 5.2, 5.5, 5.7
    
    - **semester_id**: ID of the semester (required, must exist)
    - **name**: Teaching unit name (required)
    - **name_de**: Teaching unit name in German (optional)
    - **code**: Teaching unit code (optional, e.g., "UE1", "UE2")
    - **description**: Teaching unit description in English (optional)
    - **description_de**: Teaching unit description in German (optional)
    - **ects_required**: ECTS requirements for this teaching unit (optional, non-negative)
    
    Returns:
        The created teaching unit with all fields including ID and timestamps
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If semester not found
        400: If validation fails (duplicate code, invalid ECTS)
    """
    # Apply RBAC - only Super Admin can create teaching units
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can create teaching units"
        )
    
    # Create teaching unit using service
    service = TeachingUnitService(db)
    try:
        teaching_unit = await service.create_teaching_unit(teaching_unit_data.model_dump())
        
        # Log creation in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="teaching_unit",
            entity_id=teaching_unit.id,
            data=teaching_unit_data.model_dump(),
            user_id=current_user.id
        )
        
        return teaching_unit
        
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
    response_model=TeachingUnitListResponse,
    summary="List all teaching units",
    description="Get paginated list of teaching units with optional search and filters. Applies role-based filtering."
)
async def list_teaching_units(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by name, code, or description"),
    semester_id: Optional[int] = Query(None, description="Filter by semester ID"),
    academic_track_id: Optional[int] = Query(None, description="Filter by academic track ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of teaching units with optional filters.
    
    Requirements: 5.1-5.7
    
    Filters are applied based on user role:
    - **Super Admin**: Can see all teaching units
    - **University Admin**: Can see teaching units linked to their assigned universities
    - **Program Coordinator**: Can see teaching units for their assigned programs
    
    Query Parameters:
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    - **search**: Search in name, code, and description fields
    - **semester_id**: Filter by semester ID
    - **academic_track_id**: Filter by academic track ID
    
    Returns:
        List of teaching units with total count
    """
    # Apply RBAC - all admin roles can list teaching units
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if semester_id:
        filters["semester_id"] = semester_id
    if academic_track_id:
        filters["academic_track_id"] = academic_track_id
    
    # Get teaching units using service
    service = TeachingUnitService(db)
    teaching_units, total = await service.get_teaching_units(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return {
        "teaching_units": teaching_units,
        "total": total
    }


@router.get(
    "/{teaching_unit_id}",
    response_model=TeachingUnitResponse,
    summary="Get teaching unit details",
    description="Get detailed information about a specific teaching unit."
)
async def get_teaching_unit(
    teaching_unit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific teaching unit.
    
    Requirements: 5.1-5.7
    
    Path Parameters:
    - **teaching_unit_id**: ID of the teaching unit to retrieve
    
    Returns:
        Teaching unit details
        
    Raises:
        403: If user doesn't have access to view teaching units
        404: If teaching unit not found
    """
    # Apply RBAC - all admin roles can view teaching units
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get teaching unit using service
    service = TeachingUnitService(db)
    teaching_unit = await service.get_teaching_unit_by_id(teaching_unit_id)
    
    if not teaching_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching unit with ID {teaching_unit_id} not found"
        )
    
    return teaching_unit


@router.put(
    "/{teaching_unit_id}",
    response_model=TeachingUnitResponse,
    summary="Update teaching unit",
    description="Update teaching unit information. Only provided fields will be updated."
)
async def update_teaching_unit(
    teaching_unit_id: int,
    teaching_unit_data: TeachingUnitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update teaching unit information.
    
    Requirements: 5.3
    
    Path Parameters:
    - **teaching_unit_id**: ID of the teaching unit to update
    
    Body:
    - Only provided fields will be updated
    - All fields are optional in the update request
    
    Returns:
        Updated teaching unit details
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If teaching unit not found
        400: If validation fails (duplicate code, invalid ECTS)
    """
    # Apply RBAC - only Super Admin can update teaching units
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can update teaching units"
        )
    
    # Get before state for audit log
    service = TeachingUnitService(db)
    before_teaching_unit = await service.get_teaching_unit_by_id(teaching_unit_id)
    
    if not before_teaching_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching unit with ID {teaching_unit_id} not found"
        )
    
    # Convert to dict for audit log
    before_data = {
        "semester_id": before_teaching_unit.semester_id,
        "name": before_teaching_unit.name,
        "name_de": before_teaching_unit.name_de,
        "code": before_teaching_unit.code,
        "description": before_teaching_unit.description,
        "description_de": before_teaching_unit.description_de,
        "ects_required": before_teaching_unit.ects_required
    }
    
    # Update teaching unit using service
    try:
        # Only include fields that were actually provided
        update_data = teaching_unit_data.model_dump(exclude_unset=True)
        teaching_unit = await service.update_teaching_unit(teaching_unit_id, update_data)
        
        # Log update in audit log
        after_data = {
            "semester_id": teaching_unit.semester_id,
            "name": teaching_unit.name,
            "name_de": teaching_unit.name_de,
            "code": teaching_unit.code,
            "description": teaching_unit.description,
            "description_de": teaching_unit.description_de,
            "ects_required": teaching_unit.ects_required
        }
        
        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="teaching_unit",
            entity_id=teaching_unit_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id
        )
        
        return teaching_unit
        
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
    "/{teaching_unit_id}",
    summary="Delete teaching unit",
    description="Soft delete a teaching unit. Prevents deletion if courses are assigned."
)
async def delete_teaching_unit(
    teaching_unit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a teaching unit.
    
    Requirements: 5.4
    
    This operation:
    - Marks the teaching unit as deleted (soft delete)
    - Prevents deletion if courses are assigned
    - Returns counts of all dependent entities
    
    Path Parameters:
    - **teaching_unit_id**: ID of the teaching unit to delete
    
    Returns:
        Success message and counts of dependent entities
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If teaching unit not found
        400: If teaching unit has assigned courses
    """
    # Apply RBAC - only Super Admin can delete teaching units
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete teaching units"
        )
    
    # Get before state for audit log
    service = TeachingUnitService(db)
    teaching_unit = await service.get_teaching_unit_by_id(teaching_unit_id)
    
    if not teaching_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching unit with ID {teaching_unit_id} not found"
        )
    
    before_data = {
        "name": teaching_unit.name,
        "name_de": teaching_unit.name_de,
        "code": teaching_unit.code,
        "semester_id": teaching_unit.semester_id
    }
    
    # Delete teaching unit using service
    try:
        result = await service.delete_teaching_unit(teaching_unit_id)
        
        # Log deletion in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="teaching_unit",
            entity_id=teaching_unit_id,
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
    "/{teaching_unit_id}/dependents",
    response_model=TeachingUnitDependentCountsResponse,
    summary="Get dependent entity counts",
    description="Get counts of all entities that depend on this teaching unit (courses)."
)
async def get_dependent_counts(
    teaching_unit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of entities dependent on this teaching unit.
    
    Requirements: 5.1-5.7
    
    Useful for validation before deletion to understand the impact.
    
    Path Parameters:
    - **teaching_unit_id**: ID of the teaching unit
    
    Returns:
        Dictionary with counts:
        - courses_count: Number of courses
        
    Raises:
        403: If user doesn't have access
        404: If teaching unit not found
    """
    # Apply RBAC - all admin roles can view dependent counts
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if teaching unit exists
    service = TeachingUnitService(db)
    teaching_unit = await service.get_teaching_unit_by_id(teaching_unit_id)
    
    if not teaching_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teaching unit with ID {teaching_unit_id} not found"
        )
    
    # Get dependent counts
    counts = await service.get_dependent_counts(teaching_unit_id)
    
    return {
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
