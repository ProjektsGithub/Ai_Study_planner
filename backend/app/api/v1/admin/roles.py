"""
Role and Permission Management API Endpoints

Provides complete CRUD operations for admin role assignments:

  GET   /api/v1/admin/roles                    — List all user role assignments (paginated)
  GET   /api/v1/admin/roles/definitions        — List all available admin role definitions
  GET   /api/v1/admin/roles/user/{user_id}     — Get all roles assigned to a user
  POST  /api/v1/admin/roles/assign             — Assign a role to a user
  PUT   /api/v1/admin/roles/{assignment_id}    — Modify an existing role assignment
  DELETE /api/v1/admin/roles/{assignment_id}   — Revoke a role assignment

Business rules:
  - A user may hold multiple role assignments (e.g., University Admin for uni A + uni B)
  - Duplicate assignments (same user + role + scope) are rejected
  - Super Admin cannot revoke their own role (prevents lockout)
  - All mutations are audit-logged

RBAC: All endpoints restricted to Super Admin.

Requirements: 11.1-11.9
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import ROLE_SUPER_ADMIN
from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.schemas.admin import (
    AdminRoleListResponse,
    AdminRoleResponse,
    UserRoleResponse,
    RoleAssignRequest,
    RoleUpdateRequest,
    RoleListResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()


# ============================================================================
# GET /api/v1/admin/roles/definitions  — List available admin roles
# ============================================================================

@router.get(
    "/definitions",
    response_model=AdminRoleListResponse,
    summary="List available admin role definitions",
    description=(
        "Return all admin role definitions (super_admin, university_admin, program_coordinator). "
        "Requires Super Admin role."
    ),
)
async def list_role_definitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all admin role definitions.

    Requirements: 11.1, 11.4

    Returns:
        AdminRoleListResponse with all AdminRole records.
    """
    await _require_super_admin(current_user, db)

    roles = db.query(AdminRole).order_by(AdminRole.name).all()
    return AdminRoleListResponse(
        roles=[AdminRoleResponse.model_validate(r) for r in roles]
    )


# ============================================================================
# GET /api/v1/admin/roles  — List all user role assignments
# ============================================================================

@router.get(
    "",
    response_model=RoleListResponse,
    summary="List all role assignments",
    description=(
        "Return a paginated list of all user-to-role assignments. "
        "Optionally filter by role name or user ID. "
        "Each assignment includes user email, role name, and scope (university/program). "
        "Requires Super Admin role."
    ),
)
async def list_role_assignments(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    user_id: Optional[int] = Query(None, gt=0, description="Filter by user ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all user role assignments with optional filters.

    Requirements: 11.4, 11.5, 11.9

    Returns:
        Paginated RoleListResponse with enriched assignment data.
    """
    await _require_super_admin(current_user, db)

    query = db.query(UserRole)

    if user_id:
        query = query.filter(UserRole.user_id == user_id)

    if role_name:
        query = query.join(AdminRole).filter(AdminRole.name == role_name)

    total = query.count()
    assignments = query.order_by(UserRole.assigned_at.desc()).offset(skip).limit(limit).all()

    # Batch-load user and role data
    user_ids = {a.user_id for a in assignments}
    role_ids = {a.role_id for a in assignments}

    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}
    roles = {r.id: r for r in db.query(AdminRole).filter(AdminRole.id.in_(role_ids)).all()}

    enriched = []
    for a in assignments:
        user = users.get(a.user_id)
        role = roles.get(a.role_id)
        enriched.append(UserRoleResponse(
            id=a.id,
            user_id=a.user_id,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
            role_id=a.role_id,
            role_name=role.name if role else None,
            role_display_name=role.display_name if role else None,
            university_id=a.university_id,
            program_id=a.program_id,
            assigned_at=a.assigned_at,
            assigned_by=a.assigned_by,
        ))

    return RoleListResponse(assignments=enriched, total=total)


# ============================================================================
# GET /api/v1/admin/roles/user/{user_id}  — Get roles for a specific user
# ============================================================================

@router.get(
    "/user/{user_id}",
    response_model=RoleListResponse,
    summary="Get role assignments for a user",
    description=(
        "Return all role assignments for a specific user. "
        "Requires Super Admin role."
    ),
)
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all role assignments for a specific user.

    Requirements: 11.4, 11.9

    Path Parameters:
    - **user_id**: ID of the user whose roles to retrieve.

    Returns:
        All role assignments for the user, enriched with role names.

    Raises:
        404: If the user is not found.
    """
    await _require_super_admin(current_user, db)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    assignments = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = {a.role_id for a in assignments}
    roles = {r.id: r for r in db.query(AdminRole).filter(AdminRole.id.in_(role_ids)).all()}

    enriched = [
        UserRoleResponse(
            id=a.id,
            user_id=a.user_id,
            user_email=target_user.email,
            user_name=target_user.name,
            role_id=a.role_id,
            role_name=roles[a.role_id].name if a.role_id in roles else None,
            role_display_name=roles[a.role_id].display_name if a.role_id in roles else None,
            university_id=a.university_id,
            program_id=a.program_id,
            assigned_at=a.assigned_at,
            assigned_by=a.assigned_by,
        )
        for a in assignments
    ]

    return RoleListResponse(assignments=enriched, total=len(enriched))


# ============================================================================
# POST /api/v1/admin/roles/assign  — Assign a role to a user
# ============================================================================

@router.post(
    "/assign",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a role to a user",
    description=(
        "Assign an admin role to a user. "
        "For 'university_admin', a university_id is required. "
        "For 'program_coordinator', a program_id is required. "
        "Duplicate assignments (same user + role + scope) are rejected. "
        "Requires Super Admin role."
    ),
)
async def assign_role(
    data: RoleAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Assign an admin role to a user.

    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6

    Body:
    - **user_id**: Target user.
    - **role_name**: 'super_admin', 'university_admin', or 'program_coordinator'.
    - **university_id**: Required for 'university_admin'.
    - **program_id**: Required for 'program_coordinator'.

    Returns:
        Created UserRole assignment with enriched user and role details.

    Raises:
        400: Scope validation error or duplicate assignment.
        404: User or role not found.
    """
    await _require_super_admin(current_user, db)

    # Validate scope requirements
    _validate_role_scope(data.role_name, data.university_id, data.program_id)

    # Verify user exists
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {data.user_id} not found",
        )

    # Resolve role definition
    role = db.query(AdminRole).filter(
        AdminRole.name == data.role_name,
        AdminRole.is_active == True,
    ).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin role '{data.role_name}' not found or inactive",
        )

    # Check for duplicate assignment (same user + role + scope)
    existing = _find_duplicate_assignment(
        db, data.user_id, role.id, data.university_id, data.program_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"User {data.user_id} already has role '{data.role_name}' "
                f"with university_id={data.university_id} and program_id={data.program_id}"
            ),
        )

    # Create assignment
    assignment = UserRole(
        user_id=data.user_id,
        role_id=role.id,
        university_id=data.university_id,
        program_id=data.program_id,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_create(
        entity_type="user_role",
        entity_id=assignment.id,
        data={
            "user_id": data.user_id,
            "user_email": target_user.email,
            "role_name": data.role_name,
            "university_id": data.university_id,
            "program_id": data.program_id,
        },
        user_id=current_user.id,
        description=f"Assigned role '{data.role_name}' to {target_user.email}",
    )

    return UserRoleResponse(
        id=assignment.id,
        user_id=assignment.user_id,
        user_email=target_user.email,
        user_name=target_user.name,
        role_id=assignment.role_id,
        role_name=role.name,
        role_display_name=role.display_name,
        university_id=assignment.university_id,
        program_id=assignment.program_id,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
    )


# ============================================================================
# PUT /api/v1/admin/roles/{assignment_id}  — Modify a role assignment
# ============================================================================

@router.put(
    "/{assignment_id}",
    response_model=UserRoleResponse,
    summary="Modify a role assignment",
    description=(
        "Update the role, university scope, or program scope of an existing assignment. "
        "Prevents modification of the calling Super Admin's own assignment. "
        "Requires Super Admin role."
    ),
)
async def update_role_assignment(
    assignment_id: int,
    data: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Modify an existing role assignment.

    Requirements: 11.4, 11.5, 11.6

    Path Parameters:
    - **assignment_id**: ID of the UserRole record to update.

    Body (all fields optional):
    - **role_name**: New role to apply.
    - **university_id**: New university scope.
    - **program_id**: New program scope.

    Returns:
        Updated UserRoleResponse.

    Raises:
        400: Scope validation error or self-modification of Super Admin role.
        404: Assignment, user, or role not found.
    """
    await _require_super_admin(current_user, db)

    assignment = _get_assignment_or_404(assignment_id, db)
    before_snapshot = _assignment_snapshot(assignment)

    # Prevent a Super Admin from downgrading their own primary role
    current_role = db.query(AdminRole).filter(AdminRole.id == assignment.role_id).first()
    if (
        assignment.user_id == current_user.id
        and current_role
        and current_role.name == ROLE_SUPER_ADMIN
        and data.role_name
        and data.role_name != ROLE_SUPER_ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin cannot downgrade their own role. Ask another Super Admin to do this.",
        )

    # Resolve new role if changing
    new_role = current_role
    if data.role_name and data.role_name != (current_role.name if current_role else None):
        new_role = db.query(AdminRole).filter(
            AdminRole.name == data.role_name, AdminRole.is_active == True
        ).first()
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin role '{data.role_name}' not found or inactive",
            )
        assignment.role_id = new_role.id

    # Update scope
    new_uni_id = data.university_id if data.university_id is not None else assignment.university_id
    new_prog_id = data.program_id if data.program_id is not None else assignment.program_id

    target_role_name = new_role.name if new_role else ROLE_SUPER_ADMIN
    _validate_role_scope(target_role_name, new_uni_id, new_prog_id)

    assignment.university_id = new_uni_id
    assignment.program_id = new_prog_id
    db.commit()
    db.refresh(assignment)

    target_user = db.query(User).filter(User.id == assignment.user_id).first()
    after_snapshot = _assignment_snapshot(assignment)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_update(
        entity_type="user_role",
        entity_id=assignment_id,
        before=before_snapshot,
        after=after_snapshot,
        user_id=current_user.id,
        description=f"Modified role assignment {assignment_id} for user {assignment.user_id}",
    )

    return UserRoleResponse(
        id=assignment.id,
        user_id=assignment.user_id,
        user_email=target_user.email if target_user else None,
        user_name=target_user.name if target_user else None,
        role_id=assignment.role_id,
        role_name=new_role.name if new_role else None,
        role_display_name=new_role.display_name if new_role else None,
        university_id=assignment.university_id,
        program_id=assignment.program_id,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
    )


# ============================================================================
# DELETE /api/v1/admin/roles/{assignment_id}  — Revoke a role assignment
# ============================================================================

@router.delete(
    "/{assignment_id}",
    summary="Revoke a role assignment",
    description=(
        "Permanently remove a role assignment from a user. "
        "Super Admin cannot revoke their own Super Admin assignment (prevents lockout). "
        "Requires Super Admin role."
    ),
)
async def revoke_role_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke (permanently delete) a role assignment.

    Requirements: 11.4, 11.6

    Path Parameters:
    - **assignment_id**: ID of the UserRole record to delete.

    Returns:
        Success message.

    Raises:
        400: If Super Admin attempts to revoke their own Super Admin role.
        404: If assignment not found.
    """
    await _require_super_admin(current_user, db)

    assignment = _get_assignment_or_404(assignment_id, db)
    current_role = db.query(AdminRole).filter(AdminRole.id == assignment.role_id).first()
    before_snapshot = _assignment_snapshot(assignment)

    # Lockout prevention
    if (
        assignment.user_id == current_user.id
        and current_role
        and current_role.name == ROLE_SUPER_ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin cannot revoke their own Super Admin role. Ask another Super Admin.",
        )

    target_user = db.query(User).filter(User.id == assignment.user_id).first()
    role_name = current_role.name if current_role else "unknown"

    db.delete(assignment)
    db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_delete(
        entity_type="user_role",
        entity_id=assignment_id,
        data=before_snapshot,
        user_id=current_user.id,
        description=(
            f"Revoked role '{role_name}' from "
            f"{target_user.email if target_user else assignment.user_id}"
        ),
    )

    return {
        "success": True,
        "message": (
            f"Role '{role_name}' revoked from "
            f"{target_user.email if target_user else f'user {assignment.user_id}'}"
        ),
    }


# ============================================================================
# Helpers
# ============================================================================

def _validate_role_scope(
    role_name: str,
    university_id: Optional[int],
    program_id: Optional[int],
) -> None:
    """
    Enforce scope requirements per role type:
      - university_admin  → university_id required
      - program_coordinator → program_id required
      - super_admin → no scope allowed
    """
    if role_name == "university_admin" and not university_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="university_id is required when assigning the 'university_admin' role",
        )
    if role_name == "program_coordinator" and not program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="program_id is required when assigning the 'program_coordinator' role",
        )
    if role_name == "super_admin" and (university_id or program_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="super_admin role must not have a university_id or program_id scope",
        )


def _find_duplicate_assignment(
    db: Session,
    user_id: int,
    role_id: int,
    university_id: Optional[int],
    program_id: Optional[int],
) -> Optional[UserRole]:
    """Return an existing duplicate assignment or None."""
    query = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    )
    if university_id is not None:
        query = query.filter(UserRole.university_id == university_id)
    else:
        query = query.filter(UserRole.university_id == None)  # noqa: E711

    if program_id is not None:
        query = query.filter(UserRole.program_id == program_id)
    else:
        query = query.filter(UserRole.program_id == None)  # noqa: E711

    return query.first()


def _get_assignment_or_404(assignment_id: int, db: Session) -> UserRole:
    """Fetch a UserRole by ID or raise HTTP 404."""
    assignment = db.query(UserRole).filter(UserRole.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role assignment with ID {assignment_id} not found",
        )
    return assignment


def _assignment_snapshot(assignment: UserRole) -> dict:
    """Return a flat dict snapshot of a UserRole for audit logging."""
    return {
        "user_id": assignment.user_id,
        "role_id": assignment.role_id,
        "university_id": assignment.university_id,
        "program_id": assignment.program_id,
    }


async def _require_super_admin(user: User, db: Session) -> None:
    """Raise HTTP 403 if the current user is not a Super Admin."""
    from app.models.user_role import UserRole as UR
    from app.models.admin_role import AdminRole as AR

    role = (
        db.query(UR)
        .filter(UR.user_id == user.id)
        .join(AR)
        .filter(AR.name == ROLE_SUPER_ADMIN, AR.is_active == True)
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can manage role assignments",
        )
