"""
System Configuration API Endpoints

Provides GET/PUT access to platform-wide settings stored in the audit log
as a lightweight key-value store (no dedicated settings table needed):

  GET  /api/v1/admin/settings          — Get all settings grouped by category
  GET  /api/v1/admin/settings/{key}    — Get a single setting by key
  PUT  /api/v1/admin/settings          — Update one or more settings
  POST /api/v1/admin/settings/reset    — Reset all settings to defaults

Settings are stored in-memory defaults and overridden by the latest
"update" audit log entry with entity_type="system_settings".
This avoids a dedicated DB table while still providing full change history.

Supported settings (grouped by category):

  ECTS:
    default_ects_per_semester       (int, default 30)
    default_total_ects_bachelor     (int, default 180)
    default_total_ects_master       (int, default 120)
    default_total_ects_doctorate    (int, default 180)
    min_ects_per_course             (int, default 1)
    max_ects_per_course             (int, default 30)

  Security:
    max_login_attempts              (int, default 5)
    account_lockout_minutes         (int, default 30)
    min_password_length             (int, default 8)
    require_uppercase               (bool as str, default "true")
    require_special_character       (bool as str, default "true")
    session_timeout_hours           (int, default 24)

  Files:
    max_import_file_size_mb         (int, default 20)
    allowed_import_formats          (str, default "xlsx")
    max_export_rows                 (int, default 10000)

  General:
    platform_name                   (str, default "AI Study Planner Super Admin")
    support_email                   (str, default "support@ai-study-planner.de")
    maintenance_mode                (bool as str, default "false")

All updates are audit-logged. RBAC: Super Admin only.

Requirements: 20.1-20.7
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import ROLE_SUPER_ADMIN
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    SystemSettingItem,
    SystemSettingsResponse,
    SystemSettingsUpdateRequest,
)
from app.services.audit_service import AuditService

router = APIRouter()

# ---------------------------------------------------------------------------
# Default settings catalogue
# Each entry: key → {value, description, category}
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    # ECTS
    "default_ects_per_semester": {
        "value": "30",
        "description": "Default ECTS credits per semester",
        "category": "ects",
    },
    "default_total_ects_bachelor": {
        "value": "180",
        "description": "Default total ECTS required for a Bachelor's degree",
        "category": "ects",
    },
    "default_total_ects_master": {
        "value": "120",
        "description": "Default total ECTS required for a Master's degree",
        "category": "ects",
    },
    "default_total_ects_doctorate": {
        "value": "180",
        "description": "Default total ECTS required for a Doctorate degree",
        "category": "ects",
    },
    "min_ects_per_course": {
        "value": "1",
        "description": "Minimum ECTS credits allowed per course",
        "category": "ects",
    },
    "max_ects_per_course": {
        "value": "30",
        "description": "Maximum ECTS credits allowed per course",
        "category": "ects",
    },
    # Security
    "max_login_attempts": {
        "value": "5",
        "description": "Maximum failed login attempts before account lockout",
        "category": "security",
    },
    "account_lockout_minutes": {
        "value": "30",
        "description": "Duration in minutes of account lockout after max failed attempts",
        "category": "security",
    },
    "min_password_length": {
        "value": "8",
        "description": "Minimum required password length",
        "category": "security",
    },
    "require_uppercase": {
        "value": "true",
        "description": "Require at least one uppercase letter in passwords (true/false)",
        "category": "security",
    },
    "require_special_character": {
        "value": "true",
        "description": "Require at least one special character in passwords (true/false)",
        "category": "security",
    },
    "session_timeout_hours": {
        "value": "24",
        "description": "User session timeout in hours",
        "category": "security",
    },
    # Files
    "max_import_file_size_mb": {
        "value": "20",
        "description": "Maximum allowed Excel import file size in megabytes",
        "category": "files",
    },
    "allowed_import_formats": {
        "value": "xlsx",
        "description": "Comma-separated list of allowed import file extensions",
        "category": "files",
    },
    "max_export_rows": {
        "value": "10000",
        "description": "Maximum number of rows included in a single export",
        "category": "files",
    },
    # General
    "platform_name": {
        "value": "AI Study Planner Super Admin",
        "description": "Display name of the platform shown in exports and emails",
        "category": "general",
    },
    "support_email": {
        "value": "support@ai-study-planner.de",
        "description": "Support email address shown to admins",
        "category": "general",
    },
    "maintenance_mode": {
        "value": "false",
        "description": "When 'true', the platform shows a maintenance banner to non-super-admins",
        "category": "general",
    },
}

# Keys that cannot be set to an empty string
_REQUIRED_KEYS = {
    "default_ects_per_semester", "max_login_attempts", "min_password_length",
    "session_timeout_hours", "max_import_file_size_mb",
}


# ============================================================================
# GET /api/v1/admin/settings  — Get all settings
# ============================================================================

@router.get(
    "",
    response_model=SystemSettingsResponse,
    summary="Get all system settings",
    description=(
        "Return all platform-wide system settings grouped by category. "
        "Values reflect the latest update recorded in the audit log, "
        "falling back to the built-in defaults. "
        "Requires Super Admin role."
    ),
)
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all system settings (merged: defaults + latest overrides).

    Requirements: 20.1, 20.2, 20.7

    Returns:
        SystemSettingsResponse with all settings and their current values.
    """
    await _require_super_admin(current_user, db)

    current, meta = _load_current_settings(db)

    items = []
    for key, default_meta in _DEFAULTS.items():
        items.append(SystemSettingItem(
            key=key,
            value=current.get(key, default_meta["value"]),
            description=default_meta["description"],
            category=default_meta["category"],
            updated_at=meta.get("updated_at"),
            updated_by=meta.get("updated_by"),
        ))

    return SystemSettingsResponse(
        settings=items,
        total=len(items),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# GET /api/v1/admin/settings/{key}  — Get a single setting
# ============================================================================

@router.get(
    "/{key}",
    response_model=SystemSettingItem,
    summary="Get a single system setting",
    description=(
        "Return the current value of a specific system setting by key. "
        "Requires Super Admin role."
    ),
)
async def get_setting(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a single system setting by key.

    Requirements: 20.1

    Path Parameters:
    - **key**: Setting key (e.g. 'max_login_attempts').

    Returns:
        SystemSettingItem with current value, description, and category.

    Raises:
        404: If the key is not a recognised setting.
    """
    await _require_super_admin(current_user, db)

    if key not in _DEFAULTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found. Valid keys: {', '.join(sorted(_DEFAULTS.keys()))}",
        )

    current, meta = _load_current_settings(db)
    default_meta = _DEFAULTS[key]

    return SystemSettingItem(
        key=key,
        value=current.get(key, default_meta["value"]),
        description=default_meta["description"],
        category=default_meta["category"],
        updated_at=meta.get("updated_at"),
        updated_by=meta.get("updated_by"),
    )


# ============================================================================
# PUT /api/v1/admin/settings  — Update settings
# ============================================================================

@router.put(
    "",
    response_model=SystemSettingsResponse,
    summary="Update system settings",
    description=(
        "Update one or more system settings. "
        "Only the provided keys are updated — others remain unchanged. "
        "All changes are audit-logged with before/after values. "
        "Requires Super Admin role."
    ),
)
async def update_settings(
    data: SystemSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update one or more system settings.

    Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7

    Body:
    - **updates**: Dict of {setting_key: new_value_string}

    Returns:
        Updated SystemSettingsResponse with all current settings.

    Raises:
        400: If an unknown key or invalid value is provided.
    """
    await _require_super_admin(current_user, db)

    current, _ = _load_current_settings(db)

    # Validate all keys first
    unknown = [k for k in data.updates if k not in _DEFAULTS]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown setting keys: {', '.join(unknown)}. "
                f"Valid keys: {', '.join(sorted(_DEFAULTS.keys()))}"
            ),
        )

    # Validate values
    for key, raw_value in data.updates.items():
        value = str(raw_value).strip()

        if key in _REQUIRED_KEYS and not value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Setting '{key}' cannot be empty",
            )

        # Bool fields must be "true" or "false"
        bool_fields = {"require_uppercase", "require_special_character", "maintenance_mode"}
        if key in bool_fields and value.lower() not in ("true", "false"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Setting '{key}' must be 'true' or 'false', got: '{value}'",
            )

        # Integer fields must parse as positive int
        int_fields = {
            "default_ects_per_semester", "default_total_ects_bachelor",
            "default_total_ects_master", "default_total_ects_doctorate",
            "min_ects_per_course", "max_ects_per_course",
            "max_login_attempts", "account_lockout_minutes",
            "min_password_length", "session_timeout_hours",
            "max_import_file_size_mb", "max_export_rows",
        }
        if key in int_fields:
            try:
                int_val = int(value)
                if int_val < 1:
                    raise ValueError
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Setting '{key}' must be a positive integer, got: '{value}'",
                )

    # Build before snapshot and apply updates
    before_snapshot = dict(current)
    merged = {**current}
    for key, raw_value in data.updates.items():
        merged[key] = str(raw_value).strip()

    # Persist the updated settings blob as an audit log entry
    now = datetime.now(timezone.utc)
    audit_service = AuditService(db)
    await audit_service.log_update(
        entity_type="system_settings",
        entity_id=0,
        before=before_snapshot,
        after=merged,
        user_id=current_user.id,
        description=f"Updated {len(data.updates)} system setting(s): {', '.join(data.updates.keys())}",
    )

    # Return the full settings list with the new values
    items = []
    for key, default_meta in _DEFAULTS.items():
        items.append(SystemSettingItem(
            key=key,
            value=merged.get(key, default_meta["value"]),
            description=default_meta["description"],
            category=default_meta["category"],
            updated_at=now.isoformat(),
            updated_by=current_user.email,
        ))

    return SystemSettingsResponse(
        settings=items,
        total=len(items),
        generated_at=now.isoformat(),
    )


# ============================================================================
# POST /api/v1/admin/settings/reset  — Reset all settings to defaults
# ============================================================================

@router.post(
    "/reset",
    response_model=SystemSettingsResponse,
    summary="Reset all settings to defaults",
    description=(
        "Reset all system settings to their built-in default values. "
        "This action is audit-logged. "
        "Requires Super Admin role."
    ),
)
async def reset_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reset all system settings to their built-in defaults.

    Requirements: 20.6

    Returns:
        SystemSettingsResponse with all settings at their default values.
    """
    await _require_super_admin(current_user, db)

    current, _ = _load_current_settings(db)
    defaults = {key: meta["value"] for key, meta in _DEFAULTS.items()}

    now = datetime.now(timezone.utc)
    audit_service = AuditService(db)
    await audit_service.log_update(
        entity_type="system_settings",
        entity_id=0,
        before=current,
        after=defaults,
        user_id=current_user.id,
        description="Reset all system settings to factory defaults",
    )

    items = [
        SystemSettingItem(
            key=key,
            value=meta["value"],
            description=meta["description"],
            category=meta["category"],
            updated_at=now.isoformat(),
            updated_by=current_user.email,
        )
        for key, meta in _DEFAULTS.items()
    ]

    return SystemSettingsResponse(
        settings=items,
        total=len(items),
        generated_at=now.isoformat(),
    )


# ============================================================================
# Helpers
# ============================================================================

def _load_current_settings(db: Session) -> tuple[dict, dict]:
    """
    Load the most recent settings override from the audit log.

    Queries the most recent 'system_settings' audit log entry (operation='update')
    and merges its after_value with the built-in defaults.

    Returns:
        (merged_settings_dict, meta_dict)
        meta_dict contains 'updated_at' and 'updated_by' strings (or None).
    """
    latest = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "system_settings",
            AuditLog.operation == "update",
        )
        .order_by(AuditLog.timestamp.desc())
        .first()
    )

    defaults = {key: meta["value"] for key, meta in _DEFAULTS.items()}

    if not latest or not latest.after_value:
        return defaults, {}

    # Merge: only override keys that are still valid
    merged = dict(defaults)
    for key, value in latest.after_value.items():
        if key in _DEFAULTS:
            merged[key] = str(value)

    # Resolve updater email
    updated_by = None
    if latest.user_id:
        user = db.query(User).filter(User.id == latest.user_id).first()
        updated_by = user.email if user else str(latest.user_id)

    meta = {
        "updated_at": latest.timestamp.isoformat(),
        "updated_by": updated_by,
    }

    return merged, meta


async def _require_super_admin(user: User, db: Session) -> None:
    """Raise HTTP 403 if the current user is not a Super Admin."""
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
            detail="Only Super Admin can manage system settings",
        )
