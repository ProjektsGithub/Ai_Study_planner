"""
University Management API Endpoints

Provides REST API endpoints for managing universities including:
- Creating, reading, updating, and deleting universities
- Listing universities with filters and pagination
- Checking dependent entity counts before deletion
- RBAC middleware applied to all endpoints

Requirements: 1.1-1.7
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
    UniversityCreate,
    UniversityUpdate,
    UniversityResponse,
    UniversityListResponse,
    UniversityWithCampusesResponse
)
from app.services.university_service import UniversityService
from app.services.audit_service import AuditService


router = APIRouter()


@router.post(
    "",
    response_model=UniversityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new university",
    description="Create a new university with name, country, and optional German translation. Requires Super Admin role."
)
async def create_university(
    university_data: UniversityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new university.
    
    Requirements: 1.1, 1.7
    
    - **name**: University name in English (required, 1-255 characters, must be unique)
    - **name_de**: University name in German (optional)
    - **country**: Country where university is located (default: "Germany")
    - **description**: University description in English (optional)
    - **description_de**: University description in German (optional)
    
    Returns:
        The created university with all fields including ID and timestamps
        
    Raises:
        403: If user doesn't have Super Admin role
        409: If university name already exists
    """
    # Apply RBAC - only Super Admin can create universities
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can create universities"
        )
    
    # Create university using service
    service = UniversityService(db)
    try:
        university = await service.create_university(university_data.model_dump())
        
        # Log creation in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="university",
            entity_id=university.id,
            data=university_data.model_dump(),
            user_id=current_user.id
        )
        
        return university
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get(
    "",
    response_model=UniversityListResponse,
    summary="List all universities",
    description="Get paginated list of universities with optional search and filters. Applies role-based filtering."
)
async def list_universities(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by name or description"),
    country: Optional[str] = Query(None, description="Filter by country"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of universities with optional filters.
    
    Requirements: 1.4, 11.9
    
    Filters are applied based on user role:
    - **Super Admin**: Can see all universities
    - **University Admin**: Can only see their assigned universities
    - **Program Coordinator**: Can see universities containing their programs
    
    Query Parameters:
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    - **search**: Search in name and description fields
    - **country**: Filter by country name
    
    Returns:
        List of universities with total count
    """
    # Apply RBAC - all admin roles can list universities
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get accessible universities based on role
    accessible_university_ids = get_accessible_universities(current_user, db)
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if country:
        filters["country"] = country
    if accessible_university_ids is not None:  # None means access to all (Super Admin)
        filters["ids"] = accessible_university_ids
    
    # Get universities using service
    service = UniversityService(db)
    universities, total = await service.get_universities(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return {
        "universities": universities,
        "total": total
    }


@router.get(
    "/{university_id}",
    response_model=UniversityWithCampusesResponse,
    summary="Get university details",
    description="Get detailed information about a specific university including its campuses."
)
async def get_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific university.
    
    Requirements: 1.4, 11.7
    
    Path Parameters:
    - **university_id**: ID of the university to retrieve
    
    Returns:
        University details including campuses
        
    Raises:
        403: If user doesn't have access to this university
        404: If university not found
    """
    # Apply RBAC - check university access
    if not check_university_access(current_user, university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {university_id}"
        )
    
    # Get university using service
    service = UniversityService(db)
    university = await service.get_university_by_id(university_id)
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University with ID {university_id} not found"
        )
    
    return university


@router.put(
    "/{university_id}",
    response_model=UniversityResponse,
    summary="Update university",
    description="Update university information. Only provided fields will be updated."
)
async def update_university(
    university_id: int,
    university_data: UniversityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update university information.
    
    Requirements: 1.2, 1.7, 11.7
    
    Path Parameters:
    - **university_id**: ID of the university to update
    
    Body:
    - Only provided fields will be updated
    - All fields are optional in the update request
    
    Returns:
        Updated university details
        
    Raises:
        403: If user doesn't have access to this university
        404: If university not found
        409: If name conflicts with existing university
    """
    # Apply RBAC - check university access
    if not check_university_access(current_user, university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {university_id}"
        )
    
    # Get before state for audit log
    service = UniversityService(db)
    before_university = await service.get_university_by_id(university_id)
    
    if not before_university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University with ID {university_id} not found"
        )
    
    # Convert to dict for audit log
    before_data = {
        "name": before_university.name,
        "name_de": before_university.name_de,
        "country": before_university.country,
        "description": before_university.description,
        "description_de": before_university.description_de
    }
    
    # Update university using service
    try:
        # Only include fields that were actually provided
        update_data = university_data.model_dump(exclude_unset=True)
        university = await service.update_university(university_id, update_data)
        
        # Log update in audit log
        after_data = {
            "name": university.name,
            "name_de": university.name_de,
            "country": university.country,
            "description": university.description,
            "description_de": university.description_de
        }
        
        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="university",
            entity_id=university_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id
        )
        
        return university
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete(
    "/{university_id}",
    summary="Delete university",
    description="Soft delete a university. Returns counts of dependent entities that will be affected."
)
async def delete_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a university.
    
    Requirements: 1.3, 1.5, 11.1
    
    This operation:
    - Marks the university as deleted (soft delete)
    - Also marks associated campuses as deleted
    - Returns counts of all dependent entities
    
    Path Parameters:
    - **university_id**: ID of the university to delete
    
    Returns:
        Success message and counts of dependent entities
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If university not found
    """
    # Apply RBAC - only Super Admin can delete universities
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete universities"
        )
    
    # Get before state for audit log
    service = UniversityService(db)
    university = await service.get_university_by_id(university_id)
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University with ID {university_id} not found"
        )
    
    before_data = {
        "name": university.name,
        "name_de": university.name_de,
        "country": university.country
    }
    
    # Delete university using service
    try:
        result = await service.delete_university(university_id)
        
        # Log deletion in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="university",
            entity_id=university_id,
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
    "/{university_id}/dependents",
    summary="Get dependent entity counts",
    description="Get counts of all entities that depend on this university (campuses, programs, tracks, courses)."
)
async def get_dependent_counts(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of entities dependent on this university.
    
    Requirements: 1.5
    
    Useful for validation before deletion to understand the impact.
    
    Path Parameters:
    - **university_id**: ID of the university
    
    Returns:
        Dictionary with counts:
        - campuses: Number of campuses
        - programs: Number of linked study programs
        - tracks: Number of academic tracks (through programs)
        - semesters: Number of semesters (through tracks)
        - courses: Number of courses (through semesters)
        
    Raises:
        403: If user doesn't have access to this university
        404: If university not found
    """
    # Apply RBAC - check university access
    if not check_university_access(current_user, university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {university_id}"
        )
    
    # Check if university exists
    service = UniversityService(db)
    university = await service.get_university_by_id(university_id)
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University with ID {university_id} not found"
        )
    
    # Get dependent counts
    counts = await service.get_dependent_counts(university_id)
    
    return counts


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
