"""
Prerequisite Relationship Management API Endpoints

Provides REST API endpoints for managing prerequisite relationships between courses:
- Creating prerequisite relationships (with circular dependency detection)
- Listing all prerequisite relationships (with optional filters)
- Deleting prerequisite relationships
- Pre-flight validation of a proposed relationship (cycle check without persisting)
- Retrieving the complete prerequisite chain for a course (BFS traversal)

RBAC rules:
- Super Admin + Program Coordinator: create, validate, delete
- All admin roles (+ University Admin): list, chain retrieval

Full audit logging is applied to every mutating operation.

Requirements: 7.1-7.8
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import (
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR,
)
from app.models.user import User
from app.schemas.admin import (
    PrerequisiteCreate,
    PrerequisiteResponse,
    PrerequisiteListResponse,
    PrerequisiteDeleteRequest,
    PrerequisiteValidateRequest,
    PrerequisiteValidateResponse,
    PrerequisiteChainNode,
    PrerequisiteChainResponse,
)
from app.services.prerequisite_service import PrerequisiteService
from app.services.audit_service import AuditService


router = APIRouter()


# ============================================================================
# POST /api/v1/admin/prerequisites  — Create a prerequisite relationship
# ============================================================================

@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create prerequisite relationship",
    description=(
        "Create a prerequisite relationship between two courses. "
        "Validates that both courses exist, that the prerequisite is from an earlier or same "
        "semester, and that no circular dependency is introduced. "
        "Requires Super Admin or Program Coordinator role."
    ),
)
async def create_prerequisite(
    data: PrerequisiteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a prerequisite relationship.

    Requirements: 7.1, 7.2, 7.6, 7.7, 7.8

    Body:
    - **course_id**: The course that depends on the prerequisite (required).
    - **prerequisite_id**: The course that must be completed first (required).

    Returns:
        Success message with course and prerequisite IDs.

    Raises:
        403: If user does not have the required role.
        404: If either course is not found.
        400: If the relationship already exists, semester ordering is wrong,
             or a circular dependency would be created.
    """
    if not await _check_role(
        current_user, [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR], db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can create prerequisite relationships",
        )

    service = PrerequisiteService(db)
    try:
        result = await service.create_prerequisite(data.course_id, data.prerequisite_id)

        # Audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="prerequisite",
            entity_id=0,  # Association table has no single stable PK in the service layer
            data={
                "course_id": data.course_id,
                "prerequisite_id": data.prerequisite_id,
            },
            user_id=current_user.id,
        )

        return result

    except ValueError as exc:
        _raise_value_error(exc)


# ============================================================================
# GET /api/v1/admin/prerequisites  — List prerequisite relationships
# ============================================================================

@router.get(
    "",
    response_model=PrerequisiteListResponse,
    summary="List prerequisite relationships",
    description=(
        "Get a paginated list of all prerequisite relationships. "
        "Optionally filter by course_id or prerequisite_id. "
        "All admin roles can access this endpoint."
    ),
)
async def list_prerequisites(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    course_id: Optional[int] = Query(
        None, gt=0, description="Filter relationships where this course is the dependent"
    ),
    prerequisite_id: Optional[int] = Query(
        None, gt=0, description="Filter relationships where this course is the prerequisite"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all prerequisite relationships.

    Requirements: 7.1

    Query Parameters:
    - **skip**: Pagination offset (default 0).
    - **limit**: Max records to return (default 100, max 1000).
    - **course_id**: Optional — show only relationships where this course is the dependent.
    - **prerequisite_id**: Optional — show only relationships where this course is the prerequisite.

    Returns:
        Paginated list of prerequisite relationships with total count.
    """
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    filters: dict = {}
    if course_id:
        filters["course_id"] = course_id
    if prerequisite_id:
        filters["prerequisite_id"] = prerequisite_id

    service = PrerequisiteService(db)
    prerequisites, total = await service.get_prerequisites(
        skip=skip, limit=limit, filters=filters
    )

    return {"prerequisites": prerequisites, "total": total}


# ============================================================================
# DELETE /api/v1/admin/prerequisites/{prerequisite_rel_id}  — Delete by ID
# ============================================================================

@router.delete(
    "/{prerequisite_rel_id}",
    summary="Delete prerequisite relationship by record ID",
    description=(
        "Delete a specific prerequisite relationship using its record ID from the "
        "course_prerequisites table. Requires Super Admin or Program Coordinator role."
    ),
)
async def delete_prerequisite_by_id(
    prerequisite_rel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a prerequisite relationship by its row ID.

    Requirements: 7.3

    Path Parameters:
    - **prerequisite_rel_id**: The row ID of the prerequisite record in the association table.

    Returns:
        Success message.

    Raises:
        403: If user does not have the required role.
        404: If the prerequisite relationship is not found.
    """
    if not await _check_role(
        current_user, [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR], db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can delete prerequisite relationships",
        )

    service = PrerequisiteService(db)

    # Retrieve the record to get course_id and prerequisite_id for the service call
    from app.models.course import course_prerequisites
    row = db.execute(
        course_prerequisites.select().where(
            course_prerequisites.c.id == prerequisite_rel_id
        )
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prerequisite relationship with ID {prerequisite_rel_id} not found",
        )

    course_id = row.course_id
    prereq_id = row.prerequisite_id

    try:
        result = await service.delete_prerequisite(course_id, prereq_id)

        # Audit log
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="prerequisite",
            entity_id=prerequisite_rel_id,
            data={"course_id": course_id, "prerequisite_id": prereq_id},
            user_id=current_user.id,
        )

        return result

    except ValueError as exc:
        _raise_value_error(exc)


# ============================================================================
# POST /api/v1/admin/prerequisites/validate  — Validate (no persistence)
# ============================================================================

@router.post(
    "/validate",
    response_model=PrerequisiteValidateResponse,
    summary="Validate a prerequisite relationship",
    description=(
        "Pre-flight check: validate whether a proposed prerequisite relationship "
        "would introduce a circular dependency, without actually persisting it. "
        "Returns the cycle path when is_valid=False so the caller can display it to the user."
    ),
)
async def validate_prerequisite(
    data: PrerequisiteValidateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate a proposed prerequisite relationship without creating it.

    Requirements: 7.2, 7.8

    Body:
    - **course_id**: The course that would depend on the prerequisite.
    - **prerequisite_id**: The proposed prerequisite course.

    Returns:
        Validation result with is_valid flag and, on failure, the circular path
        expressed as course names and IDs.

    Raises:
        403: If user does not have access.
    """
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    service = PrerequisiteService(db)
    is_valid, error_message = await service.validate_prerequisite(
        data.course_id, data.prerequisite_id
    )

    # Extract human-readable cycle path from the error message when present
    cycle_path: Optional[List[str]] = None
    if not is_valid and error_message:
        # The service embeds "Cycle path: A -> B -> C" in the message
        if "Cycle path:" in error_message:
            path_part = error_message.split("Cycle path:")[-1]
            # Strip the "(IDs: ...)" portion if present
            if "(IDs:" in path_part:
                path_part = path_part.split("(IDs:")[0]
            cycle_path = [name.strip() for name in path_part.split("->") if name.strip()]

    return PrerequisiteValidateResponse(
        is_valid=is_valid,
        course_id=data.course_id,
        prerequisite_id=data.prerequisite_id,
        error_message=error_message,
        cycle_path=cycle_path,
    )


# ============================================================================
# GET /api/v1/admin/prerequisites/chain/{course_id}  — Full chain (BFS)
# ============================================================================

@router.get(
    "/chain/{course_id}",
    response_model=PrerequisiteChainResponse,
    summary="Get complete prerequisite chain",
    description=(
        "Retrieve the full transitive prerequisite chain for a course using BFS. "
        "Each node in the result includes its depth level, course info, and which "
        "course directly depends on it. Sorted by level then semester number."
    ),
)
async def get_prerequisite_chain(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the complete prerequisite chain for a course (BFS traversal).

    Requirements: 7.4

    Path Parameters:
    - **course_id**: ID of the course to start the chain from.

    Returns:
        Full prerequisite chain ordered by depth level then semester number.

    Raises:
        403: If user does not have access.
        404: If the course is not found.
    """
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Verify the course exists first so we can return a clear 404
    from app.models.course import Course
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.is_deleted == False,
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    service = PrerequisiteService(db)
    chain_data = await service.get_prerequisite_chain(course_id)

    # Map raw dicts to typed schema nodes
    chain_nodes = [
        PrerequisiteChainNode(
            level=node["level"],
            course_id=node["course_id"],
            course_name=node["course_name"],
            course_code=node.get("course_code"),
            semester_number=node["semester_number"],
            ects_credits=node["ects_credits"],
            required_by_id=node["required_by_id"],
            required_by_name=node["required_by_name"],
        )
        for node in chain_data
    ]

    return PrerequisiteChainResponse(
        course_id=course_id,
        total_nodes=len(chain_nodes),
        chain=chain_nodes,
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _check_role(user: User, allowed_roles: List[str], db: Session) -> bool:
    """
    Check if the authenticated user holds one of the specified admin roles.

    Args:
        user: The currently authenticated user.
        allowed_roles: List of role name strings to match against.
        db: Database session.

    Returns:
        True if the user holds at least one of the allowed roles, False otherwise.
    """
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole

    user_roles = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id)
        .join(AdminRole)
        .filter(
            AdminRole.name.in_(allowed_roles),
            AdminRole.is_active == True,
        )
        .all()
    )

    return len(user_roles) > 0


def _raise_value_error(exc: ValueError) -> None:
    """
    Convert a service-layer ValueError into the appropriate HTTP exception.

    - "not found" in message  →  404 Not Found
    - anything else           →  400 Bad Request

    Args:
        exc: ValueError raised by the service layer.

    Raises:
        HTTPException: Always.
    """
    message = str(exc).lower()
    if "not found" in message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )
