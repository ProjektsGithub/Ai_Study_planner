"""
Bulk Import System API Endpoints

Provides REST API endpoints for uploading and processing Excel-based curriculum imports:

  POST  /api/v1/admin/imports/upload    — Upload an Excel file (returns a temp session token)
  POST  /api/v1/admin/imports/validate  — Validate parsed data (no DB writes)
  POST  /api/v1/admin/imports/preview   — Preview entities that would be created
  POST  /api/v1/admin/imports/execute   — Execute the import as a single transaction
  GET   /api/v1/admin/imports           — List bulk-import history from audit logs
  GET   /api/v1/admin/imports/{id}      — Get details for a specific import log entry
  POST  /api/v1/admin/imports/{id}/rollback — Rollback (soft-delete) all entities created by an import

Excel structure expected (see ImportService.parse_excel_file for details):
  Sheets: Universities, Campuses, Programs, University_Programs, Tracks,
          Semesters, TeachingUnits, Courses, Prerequisites

Workflow:
  1. Upload  → receive import_session_id
  2. Validate → fix errors in your Excel, re-upload if needed
  3. Preview  → confirm entity counts
  4. Execute  → commit to DB (one transaction, auto-rollback on failure)

RBAC: Super Admin only for all import operations.

Requirements: 9.1-9.10, 17.1-17.6
"""
import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import ROLE_SUPER_ADMIN
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.schemas.admin import (
    ImportErrorDetail,
    ImportPreviewResponse,
    ImportEntityCount,
    ImportValidateResponse,
    ImportExecuteResponse,
    ImportHistoryItem,
    ImportHistoryResponse,
    ImportRollbackResponse,
)
from app.services.import_service import ImportService
from app.services.audit_service import AuditService


router = APIRouter()

# Temp directory for uploaded files (within the project, not /tmp)
_UPLOAD_DIR = Path("uploads") / "imports"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max upload size: 20 MB
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


# ============================================================================
# POST /api/v1/admin/imports/upload  — Upload Excel file
# ============================================================================

@router.post(
    "/upload",
    summary="Upload Excel import file",
    description=(
        "Upload a curriculum Excel file (.xlsx) for bulk import. "
        "The file is saved to a temporary location and an import_session_id is returned. "
        "Use this token with /validate, /preview, and /execute. "
        "Requires Super Admin role."
    ),
)
async def upload_import_file(
    file: UploadFile = File(..., description="Excel file (.xlsx) with curriculum data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an Excel curriculum file.

    Requirements: 9.1, 9.9

    The file must be an .xlsx spreadsheet. It is stored temporarily on disk
    and identified by an import_session_id that must be passed to subsequent
    /validate, /preview, and /execute endpoints.

    Returns:
        import_session_id, filename, file_size_bytes, uploaded_at.

    Raises:
        403: If user is not Super Admin.
        400: If file format is not .xlsx or file exceeds 20 MB.
    """
    await _require_super_admin(current_user, db)

    # Validate file extension
    filename = file.filename or "upload.xlsx"
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx Excel files are supported",
        )

    # Read content with size guard
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 20 MB",
        )

    # Save to temp location
    session_id = str(uuid.uuid4())
    temp_path = _UPLOAD_DIR / f"{session_id}.xlsx"
    temp_path.write_bytes(content)

    return {
        "import_session_id": session_id,
        "filename": filename,
        "file_size_bytes": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "message": (
            "File uploaded successfully. "
            "Use the import_session_id with /validate, /preview, and /execute."
        ),
    }


# ============================================================================
# POST /api/v1/admin/imports/validate  — Validate parsed data
# ============================================================================

@router.post(
    "/validate",
    response_model=ImportValidateResponse,
    summary="Validate import data",
    description=(
        "Parse and validate the uploaded Excel file without writing to the database. "
        "Returns detailed per-row, per-sheet error messages. "
        "Requires Super Admin role."
    ),
)
async def validate_import(
    import_session_id: str = Query(..., description="Session ID returned by /upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate an uploaded import file.

    Requirements: 9.2, 9.3, 9.5, 9.6

    Query Parameters:
    - **import_session_id**: The session ID returned by /upload.

    Returns:
        is_valid flag, full error list with row numbers, and entity counts.
        Fix all errors in the Excel file and re-upload before calling /execute.

    Raises:
        403: If user is not Super Admin.
        404: If the session file is not found (re-upload required).
        400: If the file cannot be parsed (corrupted or wrong format).
    """
    await _require_super_admin(current_user, db)

    temp_path = _get_session_file_or_404(import_session_id)

    service = ImportService(db)
    try:
        import_data = service.parse_excel_file(str(temp_path))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Excel file: {str(exc)}",
        )

    is_valid, raw_errors = await service.validate_import_data(import_data)

    # Build entity count summary
    entity_counts = {
        key: len(import_data.get(key, []))
        for key in [
            "universities", "campuses", "programs", "university_programs",
            "tracks", "semesters", "teaching_units", "courses", "prerequisites",
        ]
    }

    errors = [
        ImportErrorDetail(
            row=e.get("row"),
            sheet=e.get("sheet", ""),
            message=e.get("message", ""),
            type=e.get("type", "validation"),
        )
        for e in raw_errors
    ]

    return ImportValidateResponse(
        is_valid=is_valid,
        error_count=len(errors),
        errors=errors,
        entity_counts=entity_counts,
    )


# ============================================================================
# POST /api/v1/admin/imports/preview  — Preview changes
# ============================================================================

@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Preview import changes",
    description=(
        "Parse the uploaded Excel file and return a preview of entities that would be created, "
        "including counts and up to 3 sample rows per entity type. "
        "No data is written to the database. "
        "Requires Super Admin role."
    ),
)
async def preview_import(
    import_session_id: str = Query(..., description="Session ID returned by /upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Preview the entities that would be created by an import.

    Requirements: 9.4

    Query Parameters:
    - **import_session_id**: The session ID returned by /upload.

    Returns:
        Counts and sample rows for each entity type (no DB changes).

    Raises:
        403: If user is not Super Admin.
        404: If the session file is not found (re-upload required).
        400: If the file cannot be parsed.
    """
    await _require_super_admin(current_user, db)

    temp_path = _get_session_file_or_404(import_session_id)

    service = ImportService(db)
    try:
        import_data = service.parse_excel_file(str(temp_path))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Excel file: {str(exc)}",
        )

    preview_data = await service.preview_import(import_data)

    def _make_entity_count(key: str) -> ImportEntityCount:
        section = preview_data.get(key, {})
        # Remove internal _row markers from samples
        raw_samples = section.get("samples", [])
        samples = [
            {k: v for k, v in s.items() if not k.startswith("_")}
            for s in raw_samples
        ]
        return ImportEntityCount(count=section.get("count", 0), samples=samples)

    return ImportPreviewResponse(
        universities=_make_entity_count("universities"),
        campuses=_make_entity_count("campuses"),
        programs=_make_entity_count("programs"),
        university_programs=_make_entity_count("university_programs"),
        tracks=_make_entity_count("tracks"),
        semesters=_make_entity_count("semesters"),
        teaching_units=_make_entity_count("teaching_units"),
        courses=_make_entity_count("courses"),
        prerequisites=_make_entity_count("prerequisites"),
        total_entities=preview_data.get("total_entities", 0),
    )


# ============================================================================
# POST /api/v1/admin/imports/execute  — Execute import
# ============================================================================

@router.post(
    "/execute",
    response_model=ImportExecuteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute bulk import",
    description=(
        "Execute the import as a single atomic database transaction. "
        "All entities are created in dependency order (universities → campuses → programs → "
        "tracks → semesters → teaching units → courses → prerequisites). "
        "If any error occurs, the entire transaction is rolled back — nothing is persisted. "
        "An audit log entry is created for the complete import so it can be rolled back later. "
        "Requires Super Admin role."
    ),
)
async def execute_import(
    import_session_id: str = Query(..., description="Session ID returned by /upload"),
    skip_validation: bool = Query(
        False,
        description=(
            "If False (default), validation is re-run before execution. "
            "Set to True only when /validate has already been called and the file has not changed."
        ),
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a bulk import as a single atomic database transaction.

    Requirements: 9.7, 9.8, 9.10

    Query Parameters:
    - **import_session_id**: The session ID returned by /upload.
    - **skip_validation**: Skip the pre-execute validation step (not recommended).

    Returns:
        Summary of created entities with counts and an import_id for rollback.

    Raises:
        403: If user is not Super Admin.
        404: If the session file is not found.
        400: If validation errors are present and skip_validation=False.
        500: If the import transaction fails (all changes rolled back automatically).
    """
    await _require_super_admin(current_user, db)

    temp_path = _get_session_file_or_404(import_session_id)

    service = ImportService(db)
    try:
        import_data = service.parse_excel_file(str(temp_path))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Excel file: {str(exc)}",
        )

    # Always re-validate before execute (unless explicitly skipped)
    if not skip_validation:
        is_valid, raw_errors = await service.validate_import_data(import_data)
        if not is_valid:
            errors = [
                {
                    "row": e.get("row"),
                    "sheet": e.get("sheet"),
                    "message": e.get("message"),
                    "type": e.get("type", "validation"),
                }
                for e in raw_errors
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": (
                        f"Import blocked: {len(errors)} validation error(s) found. "
                        "Fix all errors and re-upload, or call /execute with skip_validation=true."
                    ),
                    "error_count": len(errors),
                    "errors": errors[:20],  # Return first 20 for brevity
                },
            )

    # Execute the transactional import
    try:
        summary = await service.execute_import(import_data, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # Write a master audit log entry for the whole import so it can be found later
    audit_service = AuditService(db)
    import_log = await audit_service.log_create(
        entity_type="bulk_import",
        entity_id=0,
        data={
            "session_id": import_session_id,
            "created_counts": summary.get("created_counts", {}),
            "total_created": summary.get("total_created", 0),
            "filename": str(temp_path.name),
        },
        user_id=current_user.id,
    )

    # Clean up temp file after successful import
    try:
        temp_path.unlink(missing_ok=True)
    except Exception:
        pass  # Non-critical cleanup failure

    # Resolve import_id from the log object or query
    import_id: Optional[int] = None
    if import_log and hasattr(import_log, "id"):
        import_id = import_log.id
    else:
        # Fallback: query the most recent bulk_import log for this user
        latest = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "bulk_import",
                AuditLog.user_id == current_user.id,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        if latest:
            import_id = latest.id

    return ImportExecuteResponse(
        success=True,
        message=summary.get("message", "Import completed successfully"),
        import_id=import_id,
        created_counts=summary.get("created_counts", {}),
        total_created=summary.get("total_created", 0),
        timestamp=summary.get("timestamp", datetime.now(timezone.utc).isoformat()),
    )


# ============================================================================
# GET /api/v1/admin/imports  — List import history
# ============================================================================

@router.get(
    "",
    response_model=ImportHistoryResponse,
    summary="List import history",
    description=(
        "Get a paginated list of past bulk imports from the audit logs. "
        "Requires Super Admin role."
    ),
)
async def list_import_history(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a paginated history of bulk imports.

    Requirements: 9.10

    Returns:
        Paginated list of past imports with counts and timestamps.
    """
    await _require_super_admin(current_user, db)

    query = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "bulk_import")
        .order_by(AuditLog.timestamp.desc())
    )

    total = query.count()
    logs = query.offset(skip).limit(limit).all()

    items = []
    for log in logs:
        # after_value stores the import summary
        after = log.after_value or {}
        items.append(
            ImportHistoryItem(
                id=log.id,
                user_id=log.user_id,
                timestamp=log.timestamp,
                description=log.description,
                created_counts=after.get("created_counts"),
            )
        )

    return ImportHistoryResponse(imports=items, total=total)


# ============================================================================
# GET /api/v1/admin/imports/{import_id}  — Get import details
# ============================================================================

@router.get(
    "/{import_id}",
    summary="Get import details",
    description=(
        "Get full details for a specific bulk import audit log entry, "
        "including entity counts, session ID, and timestamp. "
        "Requires Super Admin role."
    ),
)
async def get_import_details(
    import_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific bulk import.

    Requirements: 9.10

    Path Parameters:
    - **import_id**: ID of the audit log entry (returned by /execute as import_id).

    Returns:
        Full import log details.

    Raises:
        403: If user is not Super Admin.
        404: If the import record is not found.
    """
    await _require_super_admin(current_user, db)

    log = _get_import_log_or_404(import_id, db)
    after = log.after_value or {}

    return {
        "id": log.id,
        "user_id": log.user_id,
        "timestamp": log.timestamp.isoformat(),
        "description": log.description,
        "session_id": after.get("session_id"),
        "filename": after.get("filename"),
        "created_counts": after.get("created_counts", {}),
        "total_created": after.get("total_created", 0),
    }


# ============================================================================
# POST /api/v1/admin/imports/{import_id}/rollback  — Rollback an import
# ============================================================================

@router.post(
    "/{import_id}/rollback",
    response_model=ImportRollbackResponse,
    summary="Rollback a bulk import",
    description=(
        "Soft-delete all entities that were created by a specific bulk import. "
        "This identifies the created entities using the audit log entries "
        "that were recorded during the import (entity_type + entity_id). "
        "Requires Super Admin role."
    ),
)
async def rollback_import(
    import_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rollback (soft-delete) all entities created by a bulk import.

    Requirements: 9.8, 9.10

    Path Parameters:
    - **import_id**: The audit log ID returned by /execute.

    Strategy:
    - Query all audit log entries with operation='create' recorded at the same timestamp
      as the master import log entry. Each entry's entity_type + entity_id identifies
      an entity to soft-delete.

    Returns:
        Summary of deleted entity counts.

    Raises:
        403: If user is not Super Admin.
        404: If the import record is not found.
        400: If the import has already been rolled back.
    """
    await _require_super_admin(current_user, db)

    log = _get_import_log_or_404(import_id, db)

    # Find all individual entity audit logs created within the same minute
    # (they share the same import timestamp window)
    import_time = log.timestamp
    time_window_start = import_time.replace(second=0, microsecond=0)
    time_window_end = import_time.replace(second=59, microsecond=999999)

    entity_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.operation == "create",
            AuditLog.user_id == log.user_id,
            AuditLog.entity_type != "bulk_import",
            AuditLog.timestamp >= time_window_start,
            AuditLog.timestamp <= time_window_end,
        )
        .all()
    )

    if not entity_logs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No entity creation logs found for this import. "
                "The import may have already been rolled back, or the audit window is too narrow."
            ),
        )

    # Soft-delete each identified entity
    deleted_counts: dict = {}
    errors: List[str] = []

    _ENTITY_MODEL_MAP = {
        "university": University,
        "campus": Campus,
        "study_program": StudyProgram,
        "academic_track": AcademicTrack,
        "semester": Semester,
        "teaching_unit": TeachingUnit,
        "course": Course,
    }

    from datetime import timezone as tz

    for entry in entity_logs:
        model_cls = _ENTITY_MODEL_MAP.get(entry.entity_type)
        if not model_cls:
            continue  # Skip unknown types (e.g., prerequisites, which have no soft-delete)

        entity = db.query(model_cls).filter(model_cls.id == entry.entity_id).first()
        if not entity:
            continue

        if hasattr(entity, "is_deleted"):
            if entity.is_deleted:
                continue  # Already deleted, skip
            entity.is_deleted = True
            if hasattr(entity, "deleted_at"):
                entity.deleted_at = datetime.now(tz.utc)

            entity_type = entry.entity_type
            deleted_counts[entity_type] = deleted_counts.get(entity_type, 0) + 1

    db.commit()

    total_deleted = sum(deleted_counts.values())

    # Audit the rollback itself
    audit_service = AuditService(db)
    await audit_service.log_delete(
        entity_type="bulk_import_rollback",
        entity_id=import_id,
        data={
            "original_import_id": import_id,
            "deleted_counts": deleted_counts,
            "total_deleted": total_deleted,
        },
        user_id=current_user.id,
    )

    return ImportRollbackResponse(
        success=True,
        message=f"Rollback completed: {total_deleted} entities soft-deleted",
        import_id=import_id,
        deleted_counts=deleted_counts,
        total_deleted=total_deleted,
    )


# ============================================================================
# POST /api/v1/admin/imports/reset  — Reset all imported data
# ============================================================================

@router.post(
    "/reset",
    summary="Reset all imported data",
    description=(
        "Soft-delete ALL universities, campuses, programs, tracks, semesters, "
        "teaching units, and courses. This is a complete reset of the curriculum data. "
        "Use with caution! Requires Super Admin role."
    ),
)
async def reset_all_data(
    confirm: bool = Query(False, description="Must be set to true to confirm reset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reset all imported curriculum data (soft-delete all entities).
    
    This endpoint performs a complete reset of:
    - All Universities
    - All Campuses
    - All Study Programs
    - All Academic Tracks
    - All Semesters
    - All Teaching Units
    - All Courses
    
    Query Parameters:
    - **confirm**: Must be set to true to confirm the reset operation.
    
    Returns:
        Summary of deleted entity counts.
    
    Raises:
        403: If user is not Super Admin.
        400: If confirmation is not provided.
    """
    await _require_super_admin(current_user, db)
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset operation requires confirmation. Set confirm=true to proceed.",
        )
    
    from datetime import timezone as tz
    
    deleted_counts = {
        "universities": 0,
        "campuses": 0,
        "programs": 0,
        "tracks": 0,
        "semesters": 0,
        "teaching_units": 0,
        "courses": 0,
    }
    
    try:
        # Soft-delete all courses
        courses = db.query(Course).filter(Course.is_deleted == False).all()
        for course in courses:
            course.is_deleted = True
            course.deleted_at = datetime.now(tz.utc)
            deleted_counts["courses"] += 1
        
        # Soft-delete all teaching units
        teaching_units = db.query(TeachingUnit).filter(TeachingUnit.is_deleted == False).all()
        for tu in teaching_units:
            tu.is_deleted = True
            tu.deleted_at = datetime.now(tz.utc)
            deleted_counts["teaching_units"] += 1
        
        # Soft-delete all semesters
        semesters = db.query(Semester).filter(Semester.is_deleted == False).all()
        for sem in semesters:
            sem.is_deleted = True
            sem.deleted_at = datetime.now(tz.utc)
            deleted_counts["semesters"] += 1
        
        # Soft-delete all tracks
        tracks = db.query(AcademicTrack).filter(AcademicTrack.is_deleted == False).all()
        for track in tracks:
            track.is_deleted = True
            track.deleted_at = datetime.now(tz.utc)
            deleted_counts["tracks"] += 1
        
        # Soft-delete all programs
        programs = db.query(StudyProgram).filter(StudyProgram.is_deleted == False).all()
        for prog in programs:
            prog.is_deleted = True
            prog.deleted_at = datetime.now(tz.utc)
            deleted_counts["programs"] += 1
        
        # Soft-delete all campuses
        campuses = db.query(Campus).filter(Campus.is_deleted == False).all()
        for campus in campuses:
            campus.is_deleted = True
            campus.deleted_at = datetime.now(tz.utc)
            deleted_counts["campuses"] += 1
        
        # Soft-delete all universities
        universities = db.query(University).filter(University.is_deleted == False).all()
        for uni in universities:
            uni.is_deleted = True
            uni.deleted_at = datetime.now(tz.utc)
            deleted_counts["universities"] += 1
        
        db.commit()
        
        total_deleted = sum(deleted_counts.values())
        
        # Audit the reset
        audit_service = AuditService(db)
        await audit_service.log_delete(
            entity_type="bulk_reset",
            entity_id=0,
            data={
                "deleted_counts": deleted_counts,
                "total_deleted": total_deleted,
            },
            user_id=current_user.id,
        )
        
        return {
            "success": True,
            "message": f"All curriculum data has been reset: {total_deleted} entities soft-deleted",
            "deleted_counts": deleted_counts,
            "total_deleted": total_deleted,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}",
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _require_super_admin(user: User, db: Session) -> None:
    """
    Raise HTTP 403 if the current user is not a Super Admin.

    Args:
        user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException 403: If user is not Super Admin.
    """
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole

    role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id)
        .join(AdminRole)
        .filter(AdminRole.name == ROLE_SUPER_ADMIN, AdminRole.is_active == True)
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can perform bulk import operations",
        )


def _get_session_file_or_404(session_id: str) -> Path:
    """
    Resolve an import session ID to its temp file path.

    Args:
        session_id: UUID session string from /upload.

    Returns:
        Path object for the temp .xlsx file.

    Raises:
        HTTPException 404: If the session file does not exist.
    """
    # Guard against path traversal
    safe_id = session_id.replace("/", "").replace("\\", "").replace("..", "")
    temp_path = _UPLOAD_DIR / f"{safe_id}.xlsx"

    if not temp_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Import session '{session_id}' not found. "
                "The file may have expired or never existed — please re-upload."
            ),
        )

    return temp_path


def _get_import_log_or_404(import_id: int, db: Session) -> AuditLog:
    """
    Fetch a bulk_import AuditLog by ID or raise HTTP 404.

    Args:
        import_id: Primary key of the audit log entry.
        db: Database session.

    Returns:
        AuditLog instance.

    Raises:
        HTTPException 404: If not found.
    """
    log = db.query(AuditLog).filter(
        AuditLog.id == import_id,
        AuditLog.entity_type == "bulk_import",
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import log with ID {import_id} not found",
        )

    return log
