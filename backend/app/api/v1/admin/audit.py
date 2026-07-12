"""
Audit Log Query API Endpoints

Provides filtered, paginated access to the administrative audit log:

  GET  /api/v1/admin/audit/logs                     — Filtered, paginated log list
  GET  /api/v1/admin/audit/logs/export              — Export to CSV or JSON download
  GET  /api/v1/admin/audit/entity/{type}/{id}       — Full change history for one entity
  GET  /api/v1/admin/audit/stats                    — Operation counts grouped by entity type

Filters supported on /logs:
  - entity_type, entity_id, operation ('create'|'update'|'delete')
  - user_id, start_date, end_date (ISO-8601)

RBAC: Super Admin only for all audit endpoints.

Requirements: 16.1-16.7
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from io import StringIO
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import ROLE_SUPER_ADMIN
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    AuditLogResponse,
    AuditLogListResponse,
    EntityHistoryResponse,
)
from app.services.audit_service import AuditService

router = APIRouter()

_ALLOWED_OPS = ["create", "update", "delete"]


# ============================================================================
# GET /api/v1/admin/audit/logs  — Filtered, paginated log list
# ============================================================================

@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="Query audit logs",
    description=(
        "Retrieve a filtered, paginated list of audit log entries. "
        "Supports filtering by entity type, entity ID, operation, user ID, and date range. "
        "Requires Super Admin role."
    ),
)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Records per page"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. 'course')"),
    entity_id: Optional[int] = Query(None, gt=0, description="Filter by entity ID"),
    operation: Optional[str] = Query(None, description="Filter: 'create', 'update', or 'delete'"),
    user_id: Optional[int] = Query(None, gt=0, description="Filter by acting user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from this timestamp (ISO-8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter up to this timestamp (ISO-8601)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get filtered, paginated audit logs.

    Requirements: 16.2, 16.3, 16.4

    Returns:
        Paginated list of audit log entries, enriched with user email.
    """
    await _require_super_admin(current_user, db)

    if operation and operation not in _ALLOWED_OPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"operation must be one of: {', '.join(_ALLOWED_OPS)}",
        )

    filters = {}
    if entity_type:
        filters["entity_type"] = entity_type
    if entity_id:
        filters["entity_id"] = entity_id
    if operation:
        filters["operation"] = operation
    if user_id:
        filters["user_id"] = user_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date

    service = AuditService(db)
    logs, total = await service.get_audit_logs(filters=filters, page=page, page_size=page_size)

    # Batch-load user emails
    user_email_map = _batch_user_emails(logs, db)

    return AuditLogListResponse(
        logs=[_enrich_log(log, user_email_map) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# GET /api/v1/admin/audit/logs/export  — Download CSV / JSON
# ============================================================================

@router.get(
    "/logs/export",
    summary="Export audit logs",
    description=(
        "Export audit logs as a downloadable CSV or JSON file. "
        "The same filters as /logs are supported. "
        "Requires Super Admin role."
    ),
)
async def export_audit_logs(
    format: str = Query("csv", description="Export format: 'csv' or 'json'"),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None, gt=0),
    operation: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None, gt=0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export audit logs to a downloadable file.

    Requirements: 16.3

    Returns:
        StreamingResponse with CSV or JSON content and Content-Disposition header.
    """
    await _require_super_admin(current_user, db)

    if format not in ("csv", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="format must be 'csv' or 'json'",
        )

    filters = {}
    if entity_type:
        filters["entity_type"] = entity_type
    if entity_id:
        filters["entity_id"] = entity_id
    if operation:
        filters["operation"] = operation
    if user_id:
        filters["user_id"] = user_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date

    service = AuditService(db)
    content = await service.export_audit_logs(filters=filters, format=format)

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{timestamp_str}.{format}"
    media_type = "text/csv" if format == "csv" else "application/json"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================================
# GET /api/v1/admin/audit/entity/{entity_type}/{entity_id}  — Entity history
# ============================================================================

@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=EntityHistoryResponse,
    summary="Get entity change history",
    description=(
        "Retrieve the full change history for a specific entity (all create/update/delete operations). "
        "Requires Super Admin role."
    ),
)
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the full audit history for a specific entity.

    Requirements: 16.2, 16.4, 16.5, 16.6, 16.7

    Path Parameters:
    - **entity_type**: e.g. 'course', 'university', 'semester'.
    - **entity_id**: Primary key of the entity.

    Returns:
        Chronological (newest-first) list of all operations performed on the entity.
    """
    await _require_super_admin(current_user, db)

    service = AuditService(db)
    logs, total = await service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        page=page,
        page_size=page_size,
    )

    user_email_map = _batch_user_emails(logs, db)

    return EntityHistoryResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        history=[_enrich_log(log, user_email_map) for log in logs],
        total=total,
    )


# ============================================================================
# GET /api/v1/admin/audit/stats  — Operation statistics by entity type
# ============================================================================

@router.get(
    "/stats",
    summary="Audit log statistics",
    description=(
        "Return the total number of audit log operations grouped by entity type. "
        "Useful for the admin dashboard. Requires Super Admin role."
    ),
)
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get audit log operation counts grouped by entity type.

    Requirements: 16.1, 16.3

    Returns:
        Dictionary mapping entity_type → operation count.
    """
    await _require_super_admin(current_user, db)

    service = AuditService(db)
    stats = await service.get_entity_type_statistics()

    return {
        "stats_by_entity_type": stats,
        "total_log_entries": sum(stats.values()),
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Helpers
# ============================================================================

def _batch_user_emails(logs: list, db: Session) -> dict:
    """Batch-load user emails for a list of AuditLog entries."""
    user_ids = {log.user_id for log in logs if log.user_id}
    if not user_ids:
        return {}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return {u.id: u.email for u in users}


def _enrich_log(log: AuditLog, user_email_map: dict) -> AuditLogResponse:
    """Convert an AuditLog ORM instance to an AuditLogResponse schema."""
    return AuditLogResponse(
        id=log.id,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        operation=log.operation,
        user_id=log.user_id,
        user_email=user_email_map.get(log.user_id) if log.user_id else None,
        timestamp=log.timestamp,
        description=log.description,
        before_value=log.before_value,
        after_value=log.after_value,
    )


async def _require_super_admin(user: User, db: Session) -> None:
    """Raise 403 if the current user is not a Super Admin."""
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
            detail="Only Super Admin can access audit logs",
        )
