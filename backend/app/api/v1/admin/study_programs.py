"""
Study Program Management API Endpoints

Provides REST API endpoints for managing study programs (Filières) including:
- Creating, reading, updating, and deleting study programs
- Linking/unlinking programs to/from universities
- Listing programs with filters and pagination
- RBAC middleware applied to all endpoints
- Audit logging for all operations

Requirements: 2.1-2.7, 17.1-17.6
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
    StudyProgramCreate,
    StudyProgramUpdate,
    StudyProgramResponse,
    StudyProgramListResponse,
    StudyProgramWithUniversitiesResponse
)
from app.services.program_service import ProgramService
from app.services.audit_service import AuditService


router = APIRouter()


@router.post(
    "",
    response_model=StudyProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new study program",
    description="Create a new study program with name, code, and optional German translation. Requires Super Admin role."
)
async def create_program(
    program_data: StudyProgramCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new study program.
    
    Requirements: 2.1, 2.5
    
    - **name**: Study program name in English (required, 1-255 characters)
    - **name_de**: Study program name in German (optional, primary language)
    - **description**: Program description in English (optional)
    - **description_de**: Program description in German (optional)
    - **code**: Program code like CS, MED, LAW (optional, must be unique, uppercase letters/numbers only)
    
    Returns:
        The created study program with all fields including ID and timestamps
        
    Raises:
        403: If user doesn't have Super Admin role
        409: If program code already exists
    """
    # Apply RBAC - only Super Admin can create programs
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can create study programs"
        )
    
    # Create program using service
    service = ProgramService(db)
    try:
        program = await service.create_program(program_data.model_dump())
        
        # Log creation in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="study_program",
            entity_id=program.id,
            data=program_data.model_dump(),
            user_id=current_user.id
        )
        
        return program
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get(
    "",
    response_model=StudyProgramListResponse,
    summary="List all study programs",
    description="Get paginated list of study programs with optional search and filters. Applies role-based filtering."
)
async def list_programs(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by name, description, or code"),
    university_id: Optional[int] = Query(None, description="Filter by university ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of study programs with optional filters.
    
    Requirements: 2.7, 11.9
    
    Filters are applied based on user role:
    - **Super Admin**: Can see all programs
    - **University Admin**: Can see programs linked to their assigned universities
    - **Program Coordinator**: Can see their assigned programs
    
    Query Parameters:
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    - **search**: Search in name, description, and code fields
    - **university_id**: Filter by linked university ID
    
    Returns:
        List of study programs with total count
    """
    # Apply RBAC - all admin roles can list programs
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if university_id:
        # Check if user has access to the university
        if not check_university_access(current_user, university_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to university {university_id}"
            )
        filters["university_id"] = university_id
    
    # Get programs using service
    service = ProgramService(db)
    programs, total = await service.get_programs(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return {
        "programs": programs,
        "total": total
    }


@router.get(
    "/{program_id}",
    response_model=StudyProgramWithUniversitiesResponse,
    summary="Get study program details",
    description="Get detailed information about a specific study program including linked universities."
)
async def get_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific study program.
    
    Requirements: 2.7, 11.7
    
    Path Parameters:
    - **program_id**: ID of the study program to retrieve
    
    Returns:
        Study program details including linked universities
        
    Raises:
        403: If user doesn't have access to view programs
        404: If program not found
    """
    # Apply RBAC - all admin roles can view programs
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get program using service
    service = ProgramService(db)
    program = await service.get_program_by_id(program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study program with ID {program_id} not found"
        )
    
    return program


@router.put(
    "/{program_id}",
    response_model=StudyProgramResponse,
    summary="Update study program",
    description="Update study program information. Only provided fields will be updated."
)
async def update_program(
    program_id: int,
    program_data: StudyProgramUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update study program information.
    
    Requirements: 2.3, 11.7
    
    Path Parameters:
    - **program_id**: ID of the study program to update
    
    Body:
    - Only provided fields will be updated
    - All fields are optional in the update request
    
    Returns:
        Updated study program details
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If program not found
        409: If code conflicts with existing program
    """
    # Apply RBAC - only Super Admin can update programs
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can update study programs"
        )
    
    # Get before state for audit log
    service = ProgramService(db)
    before_program = await service.get_program_by_id(program_id)
    
    if not before_program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study program with ID {program_id} not found"
        )
    
    # Convert to dict for audit log
    before_data = {
        "name": before_program.name,
        "name_de": before_program.name_de,
        "description": before_program.description,
        "description_de": before_program.description_de,
        "code": before_program.code
    }
    
    # Update program using service
    try:
        # Only include fields that were actually provided
        update_data = program_data.model_dump(exclude_unset=True)
        program = await service.update_program(program_id, update_data)
        
        # Log update in audit log
        after_data = {
            "name": program.name,
            "name_de": program.name_de,
            "description": program.description,
            "description_de": program.description_de,
            "code": program.code
        }
        
        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="study_program",
            entity_id=program_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id
        )
        
        return program
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete(
    "/{program_id}",
    summary="Delete study program",
    description="Soft delete a study program. Returns counts of dependent entities that will be affected."
)
async def delete_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a study program.
    
    Requirements: 2.4, 11.1
    
    This operation:
    - Marks the program as deleted (soft delete)
    - Also marks associated academic tracks as deleted
    - Returns counts of all dependent entities
    
    Path Parameters:
    - **program_id**: ID of the study program to delete
    
    Returns:
        Success message and counts of dependent entities
        
    Raises:
        403: If user doesn't have Super Admin role
        404: If program not found
    """
    # Apply RBAC - only Super Admin can delete programs
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete study programs"
        )
    
    # Get before state for audit log
    service = ProgramService(db)
    program = await service.get_program_by_id(program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study program with ID {program_id} not found"
        )
    
    before_data = {
        "name": program.name,
        "name_de": program.name_de,
        "code": program.code
    }
    
    # Delete program using service
    try:
        result = await service.delete_program(program_id)
        
        # Log deletion in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="study_program",
            entity_id=program_id,
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
    "/{program_id}/dependents",
    summary="Get dependent entity counts",
    description="Get counts of all entities that depend on this study program (universities, tracks, courses)."
)
async def get_dependent_counts(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get counts of entities dependent on this study program.
    
    Requirements: 2.4
    
    Useful for validation before deletion to understand the impact.
    
    Path Parameters:
    - **program_id**: ID of the study program
    
    Returns:
        Dictionary with counts:
        - universities: Number of linked universities
        - tracks: Number of academic tracks
        - semesters: Number of semesters (through tracks)
        - courses: Number of courses (through semesters)
        
    Raises:
        403: If user doesn't have access
        404: If program not found
    """
    # Apply RBAC - all admin roles can view dependent counts
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if program exists
    service = ProgramService(db)
    program = await service.get_program_by_id(program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study program with ID {program_id} not found"
        )
    
    # Get dependent counts
    counts = await service.get_dependent_counts(program_id)
    
    return counts


@router.get(
    "/{program_id}/universities",
    summary="Get linked universities",
    description="Get all universities linked to a specific study program."
)
async def get_linked_universities(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all universities linked to a study program.
    
    Requirements: 2.7, 17.1-17.6
    
    Path Parameters:
    - **program_id**: ID of the study program
    
    Returns:
        List of universities offering this program
        
    Raises:
        403: If user doesn't have access
        404: If program not found
    """
    # Apply RBAC - all admin roles can view linked universities
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if program exists
    service = ProgramService(db)
    program = await service.get_program_by_id(program_id)
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study program with ID {program_id} not found"
        )
    
    # Get linked universities
    universities = await service.get_universities_by_program(program_id)
    
    return {
        "universities": universities,
        "total": len(universities)
    }


@router.post(
    "/{program_id}/universities/{university_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Link program to university",
    description="Link a study program to a university. Validates that the link doesn't already exist."
)
async def link_program_to_university(
    program_id: int,
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link a study program to a university.
    
    Requirements: 2.2, 2.6, 17.1-17.6
    
    This creates a many-to-many relationship allowing:
    - One program to be offered at multiple universities
    - One university to offer multiple programs
    
    Path Parameters:
    - **program_id**: ID of the study program
    - **university_id**: ID of the university
    
    Returns:
        Success message
        
    Raises:
        403: If user doesn't have Super Admin role or access to the university
        404: If program or university not found
        409: If link already exists
    """
    # Apply RBAC - check university access
    if not check_university_access(current_user, university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {university_id}"
        )
    
    # Only Super Admin can create links
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can link programs to universities"
        )
    
    # Link program to university using service
    service = ProgramService(db)
    try:
        result = await service.link_program_to_university(program_id, university_id)
        
        # Log in audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="university_program_link",
            entity_id=program_id,
            data={"program_id": program_id, "university_id": university_id},
            user_id=current_user.id,
            description=f"Linked program {program_id} to university {university_id}"
        )
        
        return result
        
    except ValueError as e:
        # Determine appropriate status code based on error message
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )


@router.delete(
    "/{program_id}/universities/{university_id}",
    summary="Unlink program from university",
    description="Remove the link between a study program and a university."
)
async def unlink_program_from_university(
    program_id: int,
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlink a study program from a university.
    
    Requirements: 2.2, 17.1-17.6
    
    Path Parameters:
    - **program_id**: ID of the study program
    - **university_id**: ID of the university
    
    Returns:
        Success message
        
    Raises:
        403: If user doesn't have Super Admin role or access to the university
        404: If link not found
    """
    # Apply RBAC - check university access
    if not check_university_access(current_user, university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {university_id}"
        )
    
    # Only Super Admin can remove links
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can unlink programs from universities"
        )
    
    # Unlink program from university using service
    service = ProgramService(db)
    try:
        result = await service.unlink_program_from_university(program_id, university_id)
        
        # Log in audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="university_program_link",
            entity_id=program_id,
            data={"program_id": program_id, "university_id": university_id},
            user_id=current_user.id,
            description=f"Unlinked program {program_id} from university {university_id}"
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


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
