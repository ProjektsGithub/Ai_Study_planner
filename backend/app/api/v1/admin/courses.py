"""
Course Management API Endpoints

Provides REST API endpoints for managing courses (subjects) including:
- Creating, reading, updating, and deleting courses
- Advanced filtering by program, semester, ECTS range, and difficulty
- Prerequisite and dependent course retrieval
- Batch create / update / delete operations
- ECTS (1-30), coefficient (0.1-10.0), and difficulty (1-5) validation
- RBAC middleware applied to all endpoints
- Full audit logging for all mutating operations

Requirements: 6.1-6.9
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
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    CoursePrerequisitesResponse,
    CoursePrerequisiteInfo,
    CourseDependentsResponse,
    CourseDependentCountsResponse,
    CourseBatchOperation,
    CourseBatchResponse,
    CourseBatchErrorDetail,
)
from app.services.course_service import CourseService
from app.services.audit_service import AuditService


router = APIRouter()


# ============================================================================
# POST /api/v1/admin/courses  — Create a course
# ============================================================================

@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
    description=(
        "Create a new course and link it to a semester (and optionally a teaching unit). "
        "Validates ECTS (1-30), coefficient (0.1-10.0), and difficulty (1-5). "
        "Requires Super Admin or Program Coordinator role."
    ),
)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new course.

    Requirements: 6.1, 6.2, 6.3, 6.6, 6.7, 6.8, 6.9

    - **semester_id**: ID of the semester the course belongs to (required, must exist)
    - **teaching_unit_id**: ID of the teaching unit (optional)
    - **name**: Course name in English (required)
    - **name_de**: Course name in German (optional, supports ä/ö/ü/ß)
    - **code**: Unique course code e.g. CS101 (optional)
    - **ects_credits**: ECTS credits between 1 and 30 (required)
    - **coefficient**: Grade weight between 0.1 and 10.0 (required)
    - **difficulty_level**: Difficulty integer between 1 and 5 (required)

    Returns:
        The created course with all fields including ID and timestamps.

    Raises:
        403: If user does not have the required role.
        404: If semester or teaching unit not found.
        400: If validation fails (duplicate code, invalid values).
    """
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can create courses",
        )

    service = CourseService(db)
    try:
        course = await service.create_course(course_data.model_dump())

        # Audit log
        audit_service = AuditService(db)
        await audit_service.log_create(
            entity_type="course",
            entity_id=course.id,
            data=course_data.model_dump(),
            user_id=current_user.id,
        )

        return course

    except ValueError as exc:
        _raise_value_error(exc)


# ============================================================================
# GET /api/v1/admin/courses  — List courses (advanced filters)
# ============================================================================

@router.get(
    "",
    response_model=CourseListResponse,
    summary="List all courses",
    description=(
        "Get a paginated list of courses with optional advanced filters. "
        "Applies role-based filtering so University Admins and Program Coordinators "
        "see only the courses for their assigned universities/programs."
    ),
)
async def list_courses(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, name_de, code, and description"),
    semester_id: Optional[int] = Query(None, description="Filter by semester ID"),
    teaching_unit_id: Optional[int] = Query(None, description="Filter by teaching unit ID"),
    program_id: Optional[int] = Query(None, description="Filter by study program ID"),
    ects_min: Optional[int] = Query(None, ge=1, le=30, description="Minimum ECTS credits"),
    ects_max: Optional[int] = Query(None, ge=1, le=30, description="Maximum ECTS credits"),
    difficulty: Optional[int] = Query(None, ge=1, le=5, description="Exact difficulty level (1-5)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a paginated list of courses with optional filters.

    Requirements: 6.1

    All admin roles can list courses. Non-Super Admin users are limited to
    the courses within their assigned universities or programs.

    Returns:
        Paginated list of courses with total count.
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

    # Build filter dict consumed by CourseService
    filters: dict = {}
    if search:
        filters["search"] = search
    if semester_id:
        filters["semester_id"] = semester_id
    if teaching_unit_id:
        filters["teaching_unit_id"] = teaching_unit_id
    if program_id:
        filters["program_id"] = program_id
    if ects_min is not None:
        filters["ects_min"] = ects_min
    if ects_max is not None:
        filters["ects_max"] = ects_max
    if difficulty is not None:
        filters["difficulty"] = difficulty

    service = CourseService(db)
    courses, total = await service.get_courses(skip=skip, limit=limit, filters=filters)

    return {"courses": courses, "total": total}


# ============================================================================
# GET /api/v1/admin/courses/{course_id}  — Get course details
# ============================================================================

@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course details",
    description="Get detailed information about a specific course.",
)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific course.

    Requirements: 6.1

    Path Parameters:
    - **course_id**: ID of the course to retrieve.

    Returns:
        Full course details.

    Raises:
        403: If user does not have access.
        404: If course not found.
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

    service = CourseService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    return course


# ============================================================================
# PUT /api/v1/admin/courses/{course_id}  — Update a course
# ============================================================================

@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description=(
        "Update course information. Only fields that are explicitly provided will be updated. "
        "Requires Super Admin or Program Coordinator role."
    ),
)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update course information.

    Requirements: 6.4, 6.6, 6.7, 6.8

    Path Parameters:
    - **course_id**: ID of the course to update.

    Body:
    - Only provided fields will be updated (PATCH-style semantics via PUT).

    Returns:
        Updated course details.

    Raises:
        403: If user does not have the required role.
        404: If course not found.
        400: If validation fails.
    """
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can update courses",
        )

    service = CourseService(db)

    # Capture before-state for audit log
    before_course = await service.get_course_by_id(course_id)
    if not before_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    before_data = _course_audit_snapshot(before_course)

    try:
        update_data = course_data.model_dump(exclude_unset=True)
        course = await service.update_course(course_id, update_data)

        after_data = _course_audit_snapshot(course)

        audit_service = AuditService(db)
        await audit_service.log_update(
            entity_type="course",
            entity_id=course_id,
            before=before_data,
            after=after_data,
            user_id=current_user.id,
        )

        return course

    except ValueError as exc:
        _raise_value_error(exc)


# ============================================================================
# DELETE /api/v1/admin/courses/{course_id}  — Soft-delete a course
# ============================================================================

@router.delete(
    "/{course_id}",
    summary="Delete course",
    description=(
        "Soft-delete a course. Deletion is blocked if other courses depend on this course "
        "as a prerequisite. Requires Super Admin role."
    ),
)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft-delete a course.

    Requirements: 6.5

    This operation:
    - Marks the course as deleted (soft delete, retains audit history).
    - Blocks deletion if any other course lists this course as a prerequisite.
    - Returns a success message on completion.

    Path Parameters:
    - **course_id**: ID of the course to delete.

    Returns:
        Success message.

    Raises:
        403: If user does not have Super Admin role.
        404: If course not found.
        400: If the course is a prerequisite of another course.
    """
    if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can delete courses",
        )

    service = CourseService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    before_data = _course_audit_snapshot(course)

    try:
        result = await service.delete_course(course_id)

        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="course",
            entity_id=course_id,
            data=before_data,
            user_id=current_user.id,
        )

        return result

    except ValueError as exc:
        error_msg = str(exc).lower()
        if "cannot delete" in error_msg or "depend" in error_msg or "prerequisite" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ============================================================================
# GET /api/v1/admin/courses/{course_id}/prerequisites  — Get prerequisites
# ============================================================================

@router.get(
    "/{course_id}/prerequisites",
    response_model=CoursePrerequisitesResponse,
    summary="Get course prerequisites",
    description="Get all prerequisite courses for a given course (direct prerequisites only).",
)
async def get_course_prerequisites(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all direct prerequisite courses for a given course.

    Requirements: 7.4

    Path Parameters:
    - **course_id**: ID of the course.

    Returns:
        List of prerequisite courses with lightweight info.

    Raises:
        403: If user does not have access.
        404: If course not found.
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

    service = CourseService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    prerequisites = await service.get_course_prerequisites(course_id)

    return {
        "course_id": course_id,
        "prerequisites": prerequisites,
        "total": len(prerequisites),
    }


# ============================================================================
# GET /api/v1/admin/courses/{course_id}/dependents  — Get dependent courses
# ============================================================================

@router.get(
    "/{course_id}/dependents",
    response_model=CourseDependentsResponse,
    summary="Get dependent courses",
    description=(
        "Get all courses that list this course as a prerequisite. "
        "Useful to assess the impact before deleting a course."
    ),
)
async def get_course_dependents(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all courses that depend on this course as a prerequisite.

    Requirements: 7.5

    Path Parameters:
    - **course_id**: ID of the course.

    Returns:
        List of dependent courses with lightweight info.

    Raises:
        403: If user does not have access.
        404: If course not found.
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

    service = CourseService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    dependents = await service.get_course_dependents(course_id)

    return {
        "course_id": course_id,
        "dependents": dependents,
        "total": len(dependents),
    }


# ============================================================================
# POST /api/v1/admin/courses/batch  — Batch operations
# ============================================================================

@router.post(
    "/batch",
    response_model=CourseBatchResponse,
    summary="Batch course operations",
    description=(
        "Perform batch create, update, or delete operations on courses. "
        "Specify the 'operation' field as 'create', 'update', or 'delete'. "
        "Super Admin can perform all operations; Program Coordinators can create and update only."
    ),
)
async def batch_course_operations(
    batch: CourseBatchOperation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Batch create, update, or delete courses.

    Requirements: 6.1 (batch operations)

    Body:
    - **operation**: One of 'create', 'update', or 'delete'.
    - **create_items**: List of course objects to create (when operation='create').
    - **update_items**: List of objects with 'id' + partial fields (when operation='update').
    - **delete_ids**: List of course IDs to delete (when operation='delete').

    Returns:
        Summary with success_count, error_count, and per-item error details.

    Raises:
        403: If user does not have the required role.
        400: If the payload is inconsistent with the operation type.
    """
    service = CourseService(db)

    # -- DELETE: Super Admin only --
    if batch.operation == "delete":
        if not await _check_role(current_user, [ROLE_SUPER_ADMIN], db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Super Admin can perform batch delete operations",
            )
        if not batch.delete_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'delete_ids' is required for delete operations",
            )

        result = await service.batch_delete_courses(batch.delete_ids)

        # Audit each successful deletion
        audit_service = AuditService(db)
        for course_id in batch.delete_ids:
            try:
                await audit_service.log_delete(
                    entity_type="course",
                    entity_id=course_id,
                    data={"batch_delete": True},
                    user_id=current_user.id,
                )
            except Exception:
                pass  # Audit failure should not abort the response

        return CourseBatchResponse(
            operation="delete",
            success_count=result["success_count"],
            error_count=result["error_count"],
            errors=[CourseBatchErrorDetail(**e) for e in result["errors"]],
        )

    # -- CREATE / UPDATE: Super Admin or Program Coordinator --
    if not await _check_role(
        current_user,
        [ROLE_SUPER_ADMIN, ROLE_PROGRAM_COORDINATOR],
        db,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin or Program Coordinator can perform batch create/update operations",
        )

    if batch.operation == "create":
        if not batch.create_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'create_items' is required for create operations",
            )

        courses_data = [item.model_dump() for item in batch.create_items]
        result = await service.batch_create_courses(courses_data)

        # Audit each successful creation
        audit_service = AuditService(db)
        for created_id in (result.get("created_ids") or []):
            try:
                await audit_service.log_create(
                    entity_type="course",
                    entity_id=created_id,
                    data={"batch_create": True},
                    user_id=current_user.id,
                )
            except Exception:
                pass

        return CourseBatchResponse(
            operation="create",
            success_count=result["success_count"],
            error_count=result["error_count"],
            created_ids=result.get("created_ids"),
            errors=[CourseBatchErrorDetail(**e) for e in result["errors"]],
        )

    if batch.operation == "update":
        if not batch.update_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'update_items' is required for update operations",
            )

        updates = [item.model_dump() for item in batch.update_items]
        result = await service.batch_update_courses(updates)

        # Audit each successful update
        audit_service = AuditService(db)
        for item in batch.update_items:
            try:
                await audit_service.log_update(
                    entity_type="course",
                    entity_id=item.id,
                    before={"batch_update": True},
                    after=item.model_dump(exclude_unset=True),
                    user_id=current_user.id,
                )
            except Exception:
                pass

        return CourseBatchResponse(
            operation="update",
            success_count=result["success_count"],
            error_count=result["error_count"],
            errors=[CourseBatchErrorDetail(**e) for e in result["errors"]],
        )

    # Fallback — should never reach here due to Pydantic validation
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown operation: {batch.operation}",
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _check_role(user: User, allowed_roles: List[str], db: Session) -> bool:
    """
    Check if user has one of the allowed roles.

    Args:
        user: Current authenticated user.
        allowed_roles: List of role names to check against.
        db: Database session.

    Returns:
        True if user has any of the specified roles, False otherwise.
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


def _course_audit_snapshot(course) -> dict:
    """
    Return a flat dictionary snapshot of a course for audit logging.

    Args:
        course: Course ORM instance.

    Returns:
        Dictionary with key course fields.
    """
    return {
        "name": course.name,
        "name_de": course.name_de,
        "code": course.code,
        "semester_id": course.semester_id,
        "teaching_unit_id": course.teaching_unit_id,
        "ects_credits": course.ects_credits,
        "coefficient": course.coefficient,
        "difficulty_level": course.difficulty_level,
    }


def _raise_value_error(exc: ValueError) -> None:
    """
    Convert a service-layer ValueError to the appropriate HTTP exception.

    Rules:
    - "not found" in message  →  404 Not Found
    - anything else           →  400 Bad Request

    Args:
        exc: The ValueError raised by the service layer.

    Raises:
        HTTPException: Always.
    """
    if "not found" in str(exc).lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )
