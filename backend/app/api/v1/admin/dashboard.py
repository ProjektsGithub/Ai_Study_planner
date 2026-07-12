"""
Dashboard and Monitoring API Endpoints

Provides three read-only endpoints for the Super Admin Platform dashboard:

  GET  /api/v1/admin/dashboard/stats       — Aggregate statistics (9.1)
  GET  /api/v1/admin/dashboard/activities  — Recent activity feed (9.2)
  GET  /api/v1/admin/dashboard/health      — System health check (9.3)

Stats endpoint covers:
  - University & campus counts
  - Full curriculum hierarchy (programs → tracks → semesters → teaching units → courses → prerequisites)
  - Student / study plan / session counts
  - AI generation success metrics
  - Bulk import totals
  - Admin action count over last 30 days

Activities endpoint:
  - Queries the audit_logs table
  - Enriches each entry with the actor's email from the users table
  - Filters by entity_type and/or operation
  - Paginated (default 50, max 200)

Health endpoint:
  - Database connectivity probe
  - Upload directory disk space check
  - Memory utilisation via psutil (graceful degradation when unavailable)

RBAC: All three endpoints are accessible to all admin roles.

Requirements: 10.1-10.8
"""
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import (
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR,
)
from app.models.user import User
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course, course_prerequisites
from app.models.student_profile import StudentProfile
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.generation_log import GenerationLog
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    DashboardStatsResponse,
    CurriculumStats,
    StudentStats,
    AIGenerationStats,
    ImportStats,
    ActivityFeedResponse,
    ActivityItem,
    SystemHealthResponse,
    HealthCheckItem,
)

router = APIRouter()

# Path shared with the imports router
_UPLOAD_DIR = Path("uploads") / "imports"


# ============================================================================
# GET /api/v1/admin/dashboard/stats  — Aggregate statistics
# ============================================================================

@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description=(
        "Return aggregate statistics across all entities managed by the Super Admin Platform. "
        "Includes university, campus, curriculum, student, AI generation, and import counts. "
        "All admin roles can access this endpoint."
    ),
)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return aggregate statistics for the Super Admin dashboard.

    Requirements: 10.1, 10.2, 10.3, 10.4, 10.8

    Returns:
        DashboardStatsResponse with counts for all major entity groups.

    Raises:
        403: If user does not have any admin role.
    """
    await _require_admin(current_user, db)

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # ---- Structural entity counts ----
    universities = db.query(func.count(University.id)).filter(
        University.is_deleted == False
    ).scalar() or 0

    campuses = db.query(func.count(Campus.id)).filter(
        Campus.is_deleted == False
    ).scalar() or 0

    study_programs = db.query(func.count(StudyProgram.id)).filter(
        StudyProgram.is_deleted == False
    ).scalar() or 0

    academic_tracks = db.query(func.count(AcademicTrack.id)).filter(
        AcademicTrack.is_deleted == False
    ).scalar() or 0

    semesters = db.query(func.count(Semester.id)).filter(
        Semester.is_deleted == False
    ).scalar() or 0

    teaching_units = db.query(func.count(TeachingUnit.id)).filter(
        TeachingUnit.is_deleted == False
    ).scalar() or 0

    courses = db.query(func.count(Course.id)).filter(
        Course.is_deleted == False
    ).scalar() or 0

    # Count rows in the association table (no is_deleted here)
    prereq_count = db.execute(
        course_prerequisites.select().with_only_columns(
            func.count(course_prerequisites.c.id)
        )
    ).scalar() or 0

    # ---- Student / plan / session counts ----
    total_students = db.query(func.count(StudentProfile.id)).scalar() or 0

    active_plans = db.query(func.count(StudyPlan.id)).scalar() or 0

    total_sessions = db.query(func.count(StudySession.id)).scalar() or 0

    # ---- AI generation stats ----
    total_gen = db.query(func.count(GenerationLog.id)).scalar() or 0
    successful_gen = db.query(func.count(GenerationLog.id)).filter(
        GenerationLog.success == True
    ).scalar() or 0
    failed_gen = total_gen - successful_gen
    success_rate = round((successful_gen / total_gen * 100), 1) if total_gen > 0 else 0.0
    avg_duration = db.query(func.avg(GenerationLog.duration_seconds)).scalar()
    avg_duration = round(float(avg_duration), 2) if avg_duration else None

    # ---- Import stats ----
    import_logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "bulk_import"
    ).all()

    total_imports = len(import_logs)
    total_entities_imported = sum(
        (log.after_value or {}).get("total_created", 0)
        for log in import_logs
    )

    # ---- Recent admin activity (last 30 days) ----
    recent_actions = db.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= thirty_days_ago
    ).scalar() or 0

    return DashboardStatsResponse(
        universities=universities,
        campuses=campuses,
        curriculum=CurriculumStats(
            study_programs=study_programs,
            academic_tracks=academic_tracks,
            semesters=semesters,
            teaching_units=teaching_units,
            courses=courses,
            prerequisite_relationships=prereq_count,
        ),
        students=StudentStats(
            total_students=total_students,
            active_study_plans=active_plans,
            total_study_sessions=total_sessions,
        ),
        ai_generations=AIGenerationStats(
            total_generations=total_gen,
            successful_generations=successful_gen,
            failed_generations=failed_gen,
            success_rate_pct=success_rate,
            avg_duration_seconds=avg_duration,
        ),
        imports=ImportStats(
            total_imports=total_imports,
            total_entities_imported=total_entities_imported,
        ),
        recent_admin_actions_30d=recent_actions,
        generated_at=now.isoformat(),
    )


# ============================================================================
# GET /api/v1/admin/dashboard/activities  — Recent activity feed
# ============================================================================

@router.get(
    "/activities",
    response_model=ActivityFeedResponse,
    summary="Get recent admin activities",
    description=(
        "Return a paginated feed of recent administrative actions from the audit log. "
        "Each entry includes the actor's email, entity type, operation, and timestamp. "
        "Optionally filter by entity_type and/or operation. "
        "All admin roles can access this endpoint."
    ),
)
async def get_recent_activities(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    entity_type: Optional[str] = Query(
        None,
        description=(
            "Filter by entity type, e.g. 'university', 'course', 'bulk_import'. "
            "Leave empty for all types."
        ),
    ),
    operation: Optional[str] = Query(
        None,
        description="Filter by operation: 'create', 'update', or 'delete'",
    ),
    since_days: int = Query(
        30,
        ge=1,
        le=365,
        description="Only return activities from the last N days (default 30, max 365)",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated recent administrative activity feed.

    Requirements: 10.5

    Query Parameters:
    - **skip**: Pagination offset.
    - **limit**: Max records (default 50, max 200).
    - **entity_type**: Optional — filter to a specific entity type.
    - **operation**: Optional — filter to 'create', 'update', or 'delete'.
    - **since_days**: How many days back to include (default 30).

    Returns:
        Paginated list of activity records with user email, entity type, and timestamp.

    Raises:
        403: If user does not have any admin role.
    """
    await _require_admin(current_user, db)

    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    query = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if operation:
        allowed_ops = ["create", "update", "delete"]
        if operation not in allowed_ops:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"operation must be one of: {', '.join(allowed_ops)}",
            )
        query = query.filter(AuditLog.operation == operation)

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    # Batch-load user emails to avoid N+1
    user_ids = {log.user_id for log in logs if log.user_id}
    user_email_map: dict = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_email_map = {u.id: u.email for u in users}

    activities = [
        ActivityItem(
            id=log.id,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            operation=log.operation,
            user_id=log.user_id,
            user_email=user_email_map.get(log.user_id) if log.user_id else None,
            timestamp=log.timestamp,
            description=log.description,
        )
        for log in logs
    ]

    return ActivityFeedResponse(activities=activities, total=total)


# ============================================================================
# GET /api/v1/admin/dashboard/health  — System health check
# ============================================================================

@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="System health check",
    description=(
        "Probe the health of key system components: "
        "database connectivity, upload directory disk space, and memory utilisation. "
        "Returns an overall 'ok', 'degraded', or 'error' status plus per-check detail. "
        "All admin roles can access this endpoint."
    ),
)
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    System health check — database, disk, and memory.

    Requirements: 10.6

    Returns:
        SystemHealthResponse with overall status and per-check breakdown.

    Raises:
        403: If user does not have any admin role.
    """
    await _require_admin(current_user, db)

    checks: list[HealthCheckItem] = []
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # 1. Database connectivity
    # ------------------------------------------------------------------
    try:
        db.execute(func.now().select() if hasattr(func.now(), "select") else func.count(AuditLog.id).select())
        # Simple ping via a cheap query
        db.execute(AuditLog.__table__.select().limit(1))
        checks.append(HealthCheckItem(
            name="database",
            status="ok",
            message="Database is reachable",
        ))
    except Exception as exc:
        checks.append(HealthCheckItem(
            name="database",
            status="error",
            message=f"Database unreachable: {str(exc)[:120]}",
        ))

    # ------------------------------------------------------------------
    # 2. Upload directory disk space
    # ------------------------------------------------------------------
    try:
        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        disk = shutil.disk_usage(str(_UPLOAD_DIR))
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        used_pct = round((disk.used / disk.total) * 100, 1)
        value_str = f"{free_gb:.1f} GB free / {total_gb:.1f} GB total ({used_pct}% used)"

        if used_pct >= 90:
            disk_status = "error"
            disk_msg = f"Disk critically full: {used_pct}% used"
        elif used_pct >= 75:
            disk_status = "warning"
            disk_msg = f"Disk filling up: {used_pct}% used"
        else:
            disk_status = "ok"
            disk_msg = "Disk space is sufficient"

        checks.append(HealthCheckItem(
            name="disk_space",
            status=disk_status,
            message=disk_msg,
            value=value_str,
        ))
    except Exception as exc:
        checks.append(HealthCheckItem(
            name="disk_space",
            status="warning",
            message=f"Could not check disk space: {str(exc)[:120]}",
        ))

    # ------------------------------------------------------------------
    # 3. Memory utilisation (requires psutil; degrades gracefully)
    # ------------------------------------------------------------------
    try:
        import psutil  # type: ignore
        mem = psutil.virtual_memory()
        used_pct = round(mem.percent, 1)
        avail_gb = mem.available / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        value_str = f"{avail_gb:.1f} GB available / {total_gb:.1f} GB total ({used_pct}% used)"

        if used_pct >= 90:
            mem_status = "error"
            mem_msg = f"Memory critically high: {used_pct}% used"
        elif used_pct >= 75:
            mem_status = "warning"
            mem_msg = f"Memory pressure: {used_pct}% used"
        else:
            mem_status = "ok"
            mem_msg = "Memory utilisation is normal"

        checks.append(HealthCheckItem(
            name="memory",
            status=mem_status,
            message=mem_msg,
            value=value_str,
        ))
    except ImportError:
        checks.append(HealthCheckItem(
            name="memory",
            status="warning",
            message="psutil not installed — memory check unavailable",
        ))
    except Exception as exc:
        checks.append(HealthCheckItem(
            name="memory",
            status="warning",
            message=f"Memory check failed: {str(exc)[:120]}",
        ))

    # ------------------------------------------------------------------
    # Determine overall status
    # ------------------------------------------------------------------
    statuses = {c.status for c in checks}
    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses:
        overall = "degraded"
    else:
        overall = "ok"

    return SystemHealthResponse(
        status=overall,
        checks=checks,
        checked_at=now.isoformat(),
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _require_admin(user: User, db: Session) -> None:
    """
    Raise HTTP 403 if the current user does not hold any recognised admin role.

    Args:
        user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException 403: If no admin role found.
    """
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole

    allowed = [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR]

    role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id)
        .join(AdminRole)
        .filter(
            AdminRole.name.in_(allowed),
            AdminRole.is_active == True,
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: admin role required",
        )
