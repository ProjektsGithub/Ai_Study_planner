"""add_admin_platform_performance_indexes

Adds composite indexes required by the Super Admin Platform to meet the
<1 second search/query targets on the audit_logs table:

  - (entity_type, timestamp)  — speeds up settings store queries and log filtering
  - (entity_type, operation)  — speeds up dashboard stats and rollback identification
  - (user_id, timestamp)      — speeds up per-user activity counts

All indexes are created with IF NOT EXISTS logic (execute raw SQL) so this
migration is safe to run multiple times.

Revision ID: c91e34f7b201
Revises: b42401a5c708
Create Date: 2026-06-19 13:00:00.000000
"""
from typing import Sequence, Union
from alembic import op


# revision identifiers
revision: str = 'c91e34f7b201'
down_revision: Union[str, Sequence[str], None] = 'b42401a5c708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite performance indexes for the Super Admin Platform."""

    # Composite index: entity_type + timestamp
    # Used by: settings store (latest system_settings entry),
    #          dashboard activity feed, audit log filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type_timestamp
        ON audit_logs (entity_type, timestamp DESC)
    """)

    # Composite index: entity_type + operation
    # Used by: dashboard stats (bulk_import count), rollback identification
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type_operation
        ON audit_logs (entity_type, operation)
    """)

    # Composite index: user_id + timestamp
    # Used by: per-user activity count (AuditService.get_user_activity_count)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id_timestamp
        ON audit_logs (user_id, timestamp DESC)
    """)

    # Composite index: university + is_deleted (common filter pattern)
    # Used by: dashboard stats, export endpoints
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_universities_name_is_deleted
        ON universities (name, is_deleted)
    """)


def downgrade() -> None:
    """Drop composite performance indexes."""
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_entity_type_timestamp")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_entity_type_operation")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_user_id_timestamp")
    op.execute("DROP INDEX IF EXISTS ix_universities_name_is_deleted")
