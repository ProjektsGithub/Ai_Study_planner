"""
Campus Management API Endpoints

Provides CRUD operations for managing university campuses including
creation, retrieval, update, and deletion with RBAC permission enforcement.

Requirements: 1.6
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.campus import Campus
from app.schemas.admin import (
    CampusCreate,
    CampusUpdate,
    CampusResponse,
    CampusListResponse
)
from app.services.university_service import UniversityService
from app.services.audit_service import AuditService
from app.middleware.rbac import (
    require_role,
    check_university_access,
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR
)


router = APIRouter()


@router.post(
    "",
    response_model=CampusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campus",
    description="Create a new campus for a university. Requires Super Admin or University Admin role."
)
async def create_campus(
    campus_data: CampusCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new campus for a university.
    
    Requirements: 1.6
    
    **Access Control:**
    - Super Admin: Can create campuses for any university
    - University Admin: Can only create campuses for their assigned universities
    - Program Coordinator: Can only create campuses for universities containing their programs
    
    **Validation:**
    - University must exist
    - Campus name and location support German special characters (ä, ö, ü, ß)
    
    **Returns:**
    - 201: Campus created successfully
    - 400: Invalid input or validation error
    - 403: Access denied - user doesn't have permission for this university
    - 404: University not found
    """
    # Check if user has access to the university
    if not check_university_access(current_user, campus_data.university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to university {campus_data.university_id}"
        )
    
    # Create campus using service
    service = UniversityService(db)
    audit_service = AuditService(db)
    
    try:
        campus = await service.create_campus(campus_data.model_dump())
        
        # Log creation in audit log
        await audit_service.log_create(
            entity_type="campus",
            entity_id=campus.id,
            data=campus_data.model_dump(),
            user_id=current_user.id
        )
        
        return campus
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campus: {str(e)}"
        )


@router.get(
    "",
    response_model=CampusListResponse,
    summary="List campuses",
    description="Get paginated list of campuses with optional filtering by university"
)
async def list_campuses(
    university_id: Optional[int] = Query(None, description="Filter by university ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of campuses with optional filtering.
    
    Requirements: 1.6
    
    **Access Control:**
    - Super Admin: Can view all campuses
    - University Admin: Can only view campuses from their assigned universities
    - Program Coordinator: Can view campuses from universities containing their programs
    
    **Query Parameters:**
    - university_id: Optional filter by university ID
    - skip: Pagination offset (default: 0)
    - limit: Maximum records to return (default: 100, max: 500)
    
    **Returns:**
    - 200: List of campuses with total count
    - 403: Access denied if user tries to access restricted university campuses
    """
    # If university_id is specified, check access
    if university_id:
        if not check_university_access(current_user, university_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to university {university_id}"
            )
    
    service = UniversityService(db)
    
    try:
        campuses, total = await service.get_campuses(
            university_id=university_id,
            skip=skip,
            limit=limit
        )
        
        return CampusListResponse(
            campuses=campuses,
            total=total
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campuses: {str(e)}"
        )


@router.get(
    "/{campus_id}",
    response_model=CampusResponse,
    summary="Get campus details",
    description="Get detailed information about a specific campus"
)
async def get_campus(
    campus_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific campus.
    
    Requirements: 1.6
    
    **Access Control:**
    - User must have access to the campus's university
    
    **Returns:**
    - 200: Campus details
    - 403: Access denied to university
    - 404: Campus not found
    """
    # Get campus
    campus = db.query(Campus).filter(
        Campus.id == campus_id,
        Campus.is_deleted == False
    ).first()
    
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campus with ID {campus_id} not found"
        )
    
    # Check university access
    if not check_university_access(current_user, campus.university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to campus {campus_id}"
        )
    
    return campus


@router.put(
    "/{campus_id}",
    response_model=CampusResponse,
    summary="Update campus",
    description="Update an existing campus information"
)
async def update_campus(
    campus_id: int,
    campus_data: CampusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing campus.
    
    Requirements: 1.6
    
    **Access Control:**
    - Super Admin: Can update any campus
    - University Admin: Can only update campuses in their assigned universities
    - Program Coordinator: Can update campuses in universities containing their programs
    
    **Validation:**
    - Campus must exist
    - If university_id is changed, user must have access to both old and new universities
    
    **Returns:**
    - 200: Campus updated successfully
    - 400: Invalid input or validation error
    - 403: Access denied
    - 404: Campus not found
    """
    # Get existing campus
    campus = db.query(Campus).filter(
        Campus.id == campus_id,
        Campus.is_deleted == False
    ).first()
    
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campus with ID {campus_id} not found"
        )
    
    # Check access to current university
    if not check_university_access(current_user, campus.university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to campus {campus_id}"
        )
    
    # If university_id is being changed, check access to new university
    update_data = campus_data.model_dump(exclude_unset=True)
    if "university_id" in update_data and update_data["university_id"] != campus.university_id:
        if not check_university_access(current_user, update_data["university_id"], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to new university {update_data['university_id']}"
            )
    
    # Store before state for audit
    before_state = {
        "name": campus.name,
        "name_de": campus.name_de,
        "location": campus.location,
        "description": campus.description,
        "description_de": campus.description_de,
        "university_id": campus.university_id
    }
    
    # Update campus using service
    service = UniversityService(db)
    audit_service = AuditService(db)
    
    try:
        updated_campus = await service.update_campus(campus_id, update_data)
        
        # Log update in audit log
        after_state = {
            "name": updated_campus.name,
            "name_de": updated_campus.name_de,
            "location": updated_campus.location,
            "description": updated_campus.description,
            "description_de": updated_campus.description_de,
            "university_id": updated_campus.university_id
        }
        
        await audit_service.log_update(
            entity_type="campus",
            entity_id=campus_id,
            before=before_state,
            after=after_state,
            user_id=current_user.id
        )
        
        return updated_campus
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campus: {str(e)}"
        )


@router.delete(
    "/{campus_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete campus",
    description="Soft delete a campus (marks as deleted rather than removing from database)"
)
async def delete_campus(
    campus_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a campus.
    
    Requirements: 1.6
    
    **Access Control:**
    - Super Admin: Can delete any campus
    - University Admin: Can only delete campuses in their assigned universities
    - Program Coordinator: Can delete campuses in universities containing their programs
    
    **Note:** This performs a soft delete (marks as deleted) rather than physically
    removing the record, preserving audit trail.
    
    **Returns:**
    - 200: Campus deleted successfully
    - 403: Access denied
    - 404: Campus not found
    """
    # Get campus
    campus = db.query(Campus).filter(
        Campus.id == campus_id,
        Campus.is_deleted == False
    ).first()
    
    if not campus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campus with ID {campus_id} not found"
        )
    
    # Check access to university
    if not check_university_access(current_user, campus.university_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to campus {campus_id}"
        )
    
    # Store campus data for audit
    campus_data = {
        "name": campus.name,
        "name_de": campus.name_de,
        "location": campus.location,
        "university_id": campus.university_id
    }
    
    # Delete campus using service
    service = UniversityService(db)
    audit_service = AuditService(db)
    
    try:
        result = await service.delete_campus(campus_id)
        
        # Log deletion in audit log
        await audit_service.log_delete(
            entity_type="campus",
            entity_id=campus_id,
            data=campus_data,
            user_id=current_user.id
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campus: {str(e)}"
        )
