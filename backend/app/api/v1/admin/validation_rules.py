"""
Validation Rules Management API Endpoints

Provides REST API endpoints for managing ECTS validation rules per academic track:
- Creating validation rules (semester_validation, year_progression, graduation)
- Listing rules with filters (by academic track and/or rule type)
- Retrieving a single rule by ID
- Updating rules
- Soft-deleting rules
- ECTS hierarchy validation endpoint:
    graduation_ects >= year_progression_ects >= semester_validation_ects  (Req 8.6, 8.7)

RBAC rules:
- Super Admin + Program Coordinator: create, update, delete
- All admin roles: list, get, validate hierarchy

Full audit logging applied to every mutating operation.

Requirements: 8.1-8.8
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import (
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR,
)
from app.models.user import User
from app.models.validation_rule import ValidationRule, RuleType
from app.models.academic_track import AcademicTrack
from app.schemas.admin import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleResponse,
    ValidationRuleListResponse,
    EctsHierarchyValidationResponse,
)
from app.services.audit_service import AuditService
from app.services.validation_service import ValidationService


router = APIRouter()


# ============================================================================
# POST /api/v1/admin/validation-rules  — Create a validation rule
# ============================================================================

@router.post(
    "",
    response_model=ValidationRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a validation rule",
    description=(
        "Create a new ECTS validation rule for an academic track. "
        "Supported rule types: 'semester_validation', 'year_progression', 'graduation'. "
        "After creation, the ECTS hierarchy is checked (graduation >= year_progression >= semester_validation). "
        "A warning is included in the response if the hierarchy is violated. "
        "Requires Super Admin or Program Coordinator role."
    ),
)
async def create_validation_rule(
    rule_data: ValidationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new validation rule.

    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.8

    Body:
    - **academic_track_id**: ID of the academic track (required, must exist).
    - **rule_type**: One of 'semester_validation', 'year_progression', 'graduation'.
    - **name**: Rule name in English (required).
    - **minimum_ects**: Positive integer ECTS threshold (required).

    Returns:
        The created validation rule.

    Raises:
        403: If user does not have the required role.
        404: If academic track not found.
        400: If a rule of the same type already exists for this track.
    """
    if not await _check_role(
        current_user, [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR], db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can create validation rules",
        )

    # Verify academic track exists
    track = db.query(AcademicTrack).filter(
        AcademicTrack.id == rule_data.academic_track_id,
        AcademicTrack.is_deleted == False,
    ).first()

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {rule_data.academic_track_id} not found",
        )

    # Each track should have at most one rule of each type
    existing = db.query(ValidationRule).filter(
        ValidationRule.academic_track_id == rule_data.academic_track_id,
        ValidationRule.rule_type == RuleType(rule_data.rule_type),
        ValidationRule.is_deleted == False,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"A '{rule_data.rule_type}' validation rule already exists for "
                f"academic track ID {rule_data.academic_track_id}. "
                "Update the existing rule or delete it first."
            ),
        )

    # Create the rule
    rule = ValidationRule(
        academic_track_id=rule_data.academic_track_id,
        rule_type=RuleType(rule_data.rule_type),
        name=rule_data.name,
        name_de=rule_data.name_de,
        description=rule_data.description,
        description_de=rule_data.description_de,
        minimum_ects=rule_data.minimum_ects,
        additional_conditions=rule_data.additional_conditions,
        additional_conditions_de=rule_data.additional_conditions_de,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_create(
        entity_type="validation_rule",
        entity_id=rule.id,
        data=rule_data.model_dump(),
        user_id=current_user.id,
    )

    return rule


# ============================================================================
# GET /api/v1/admin/validation-rules  — List validation rules
# ============================================================================

@router.get(
    "",
    response_model=ValidationRuleListResponse,
    summary="List validation rules",
    description=(
        "Get a paginated list of validation rules. "
        "Optionally filter by academic track ID and/or rule type. "
        "All admin roles can access this endpoint."
    ),
)
async def list_validation_rules(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    academic_track_id: Optional[int] = Query(
        None, gt=0, description="Filter by academic track ID"
    ),
    rule_type: Optional[str] = Query(
        None,
        description="Filter by rule type: 'semester_validation', 'year_progression', or 'graduation'",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a paginated list of validation rules.

    Requirements: 8.1-8.8

    Query Parameters:
    - **academic_track_id**: Optional — filter to a specific track.
    - **rule_type**: Optional — filter by rule type.

    Returns:
        Paginated list of validation rules with total count.
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

    # Validate rule_type filter value if provided
    if rule_type is not None:
        allowed = ["semester_validation", "year_progression", "graduation"]
        if rule_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"rule_type must be one of: {', '.join(allowed)}",
            )

    query = db.query(ValidationRule).filter(ValidationRule.is_deleted == False)

    if academic_track_id:
        query = query.filter(ValidationRule.academic_track_id == academic_track_id)

    if rule_type:
        query = query.filter(ValidationRule.rule_type == RuleType(rule_type))

    total = query.count()
    rules = query.order_by(ValidationRule.academic_track_id, ValidationRule.rule_type).offset(skip).limit(limit).all()

    return {"rules": rules, "total": total}


# ============================================================================
# GET /api/v1/admin/validation-rules/{rule_id}  — Get a single rule
# ============================================================================

@router.get(
    "/{rule_id}",
    response_model=ValidationRuleResponse,
    summary="Get validation rule details",
    description="Get detailed information about a specific validation rule.",
)
async def get_validation_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific validation rule.

    Requirements: 8.1-8.8

    Path Parameters:
    - **rule_id**: ID of the validation rule to retrieve.

    Returns:
        Full validation rule details.

    Raises:
        403: If user does not have access.
        404: If validation rule not found.
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

    rule = _get_rule_or_404(rule_id, db)
    return rule


# ============================================================================
# PUT /api/v1/admin/validation-rules/{rule_id}  — Update a rule
# ============================================================================

@router.put(
    "/{rule_id}",
    response_model=ValidationRuleResponse,
    summary="Update validation rule",
    description=(
        "Update a validation rule. Only the fields that are explicitly provided will be updated. "
        "After the update, the ECTS hierarchy for the affected academic track is re-validated. "
        "Requires Super Admin or Program Coordinator role."
    ),
)
async def update_validation_rule(
    rule_id: int,
    rule_data: ValidationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a validation rule.

    Requirements: 8.5, 8.6, 8.7

    Path Parameters:
    - **rule_id**: ID of the validation rule to update.

    Body:
    - Only the provided fields will be updated (PATCH semantics via PUT).

    Returns:
        The updated validation rule.

    Raises:
        403: If user does not have the required role.
        404: If validation rule not found.
        400: If ECTS hierarchy becomes invalid after the update.
    """
    if not await _check_role(
        current_user, [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR], db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can update validation rules",
        )

    rule = _get_rule_or_404(rule_id, db)
    before_data = _rule_audit_snapshot(rule)

    update_fields = rule_data.model_dump(exclude_unset=True)

    # If rule_type is being updated, verify no duplicate for same track
    if "rule_type" in update_fields:
        new_rule_type = RuleType(update_fields["rule_type"])
        if new_rule_type != rule.rule_type:
            conflict = db.query(ValidationRule).filter(
                ValidationRule.academic_track_id == rule.academic_track_id,
                ValidationRule.rule_type == new_rule_type,
                ValidationRule.id != rule_id,
                ValidationRule.is_deleted == False,
            ).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"A '{update_fields['rule_type']}' rule already exists for this academic track. "
                        "Delete the existing one first."
                    ),
                )
        update_fields["rule_type"] = new_rule_type

    # Apply updates
    for field, value in update_fields.items():
        setattr(rule, field, value)

    rule.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rule)

    # Validate ECTS hierarchy after update (informational — does not block save)
    validation_service = ValidationService(db)
    is_hierarchy_valid, hierarchy_details = await validation_service.validate_ects_totals(
        db, rule.academic_track_id
    )

    after_data = _rule_audit_snapshot(rule)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_update(
        entity_type="validation_rule",
        entity_id=rule_id,
        before=before_data,
        after=after_data,
        user_id=current_user.id,
    )

    # Return 400 when ECTS hierarchy is now broken — the update was already saved,
    # so we include both the updated rule and the hierarchy error in the response
    # by raising a descriptive error.  Per Req 8.6/8.7 the platform SHALL validate.
    if not is_hierarchy_valid:
        hierarchy_errors = hierarchy_details.get("errors", [])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": (
                    "Validation rule updated, but the ECTS hierarchy for this academic track "
                    "is now invalid. Please correct the rules."
                ),
                "hierarchy_errors": hierarchy_errors,
                "rule": {
                    "id": rule.id,
                    "rule_type": rule.rule_type.value,
                    "minimum_ects": rule.minimum_ects,
                },
            },
        )

    return rule


# ============================================================================
# DELETE /api/v1/admin/validation-rules/{rule_id}  — Soft-delete a rule
# ============================================================================

@router.delete(
    "/{rule_id}",
    summary="Delete validation rule",
    description=(
        "Soft-delete a validation rule. The record is retained in the database with "
        "is_deleted=True for audit history. Requires Super Admin role."
    ),
)
async def delete_validation_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft-delete a validation rule.

    Requirements: 8.5

    Path Parameters:
    - **rule_id**: ID of the validation rule to delete.

    Returns:
        Success message.

    Raises:
        403: If user does not have Super Admin role.
        404: If validation rule not found.
    """
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete validation rules",
        )

    rule = _get_rule_or_404(rule_id, db)
    before_data = _rule_audit_snapshot(rule)

    rule.is_deleted = True
    rule.deleted_at = datetime.now(timezone.utc)
    db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_delete(
        entity_type="validation_rule",
        entity_id=rule_id,
        data=before_data,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "message": f"Validation rule '{rule.name}' has been deleted",
    }


# ============================================================================
# GET /api/v1/admin/validation-rules/track/{track_id}/validate-ects
#     — Validate ECTS hierarchy for a track
# ============================================================================

@router.get(
    "/track/{track_id}/validate-ects",
    response_model=EctsHierarchyValidationResponse,
    summary="Validate ECTS hierarchy for an academic track",
    description=(
        "Check whether the validation rules configured for an academic track satisfy the "
        "ECTS hierarchy constraint: "
        "graduation_ects >= year_progression_ects >= semester_validation_ects. "
        "This is a read-only validation endpoint — it does not modify any data."
    ),
)
async def validate_ects_hierarchy(
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate the ECTS hierarchy for a given academic track.

    Requirements: 8.6, 8.7

    Path Parameters:
    - **track_id**: ID of the academic track to validate.

    Returns:
        Validation result with is_valid flag and breakdown of ECTS values per rule type.
        When is_valid=False, the 'errors' list contains human-readable violation messages.

    Raises:
        403: If user does not have access.
        404: If the academic track is not found.
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

    # Verify the track exists
    track = db.query(AcademicTrack).filter(
        AcademicTrack.id == track_id,
        AcademicTrack.is_deleted == False,
    ).first()

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Academic track with ID {track_id} not found",
        )

    validation_service = ValidationService(db)
    is_valid, details = await validation_service.validate_ects_totals(db, track_id)

    return EctsHierarchyValidationResponse(
        is_valid=is_valid,
        track_id=track_id,
        track_name=details.get("track_name"),
        track_level=details.get("track_level"),
        graduation_ects=details.get("graduation_ects"),
        year_progression_ects=details.get("year_progression_ects"),
        semester_validation_ects=details.get("semester_validation_ects"),
        errors=details.get("errors", []),
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _get_rule_or_404(rule_id: int, db: Session) -> ValidationRule:
    """
    Fetch a non-deleted ValidationRule by ID or raise HTTP 404.

    Args:
        rule_id: Primary key of the validation rule.
        db: Database session.

    Returns:
        The ValidationRule ORM instance.

    Raises:
        HTTPException 404: If not found or soft-deleted.
    """
    rule = db.query(ValidationRule).filter(
        ValidationRule.id == rule_id,
        ValidationRule.is_deleted == False,
    ).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {rule_id} not found",
        )

    return rule


def _rule_audit_snapshot(rule: ValidationRule) -> dict:
    """
    Return a flat dictionary snapshot of a validation rule for audit logging.

    Args:
        rule: ValidationRule ORM instance.

    Returns:
        Dictionary with key rule fields.
    """
    return {
        "name": rule.name,
        "name_de": rule.name_de,
        "academic_track_id": rule.academic_track_id,
        "rule_type": rule.rule_type.value if rule.rule_type else None,
        "minimum_ects": rule.minimum_ects,
        "additional_conditions": rule.additional_conditions,
    }


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
