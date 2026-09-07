"""add completed to study_sessions

Revision ID: e7c8d9a0b1c2
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c8d9a0b1c2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add completed and completed_at columns to study_sessions table."""
    op.add_column(
        'study_sessions',
        sa.Column('completed', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )
    op.add_column(
        'study_sessions',
        sa.Column('completed_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove completed and completed_at columns from study_sessions table."""
    op.drop_column('study_sessions', 'completed_at')
    op.drop_column('study_sessions', 'completed')
