"""add_retake_semesters_to_student_profiles

Adds the `retake_semesters` JSON column to the student_profiles table.

This column stores the list of semester numbers that the student is retaking
(German Wiederholung / rattrapage system).

Example values:
  - NULL or []  : no retake semesters
  - [2]         : retaking S2 (allowed for S4 students)
  - [1, 3]      : retaking S1 and S3 (allowed for S5 students)
  - [2, 3]      : retaking S2 and S3 (allowed for S6 students)

Allowed retake rules (per German academic system):
  S4 -> can retake [S2]
  S5 -> can retake [S1, S3]
  S6 -> can retake [S2, S3]
  S1/S2/S3 -> no retake allowed

Revision ID: f2a3b8c9d401
Revises: c91e34f7b201
Create Date: 2026-07-14 22:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers
revision: str = 'f2a3b8c9d401'
down_revision: Union[str, Sequence[str], None] = 'c91e34f7b201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add retake_semesters column to student_profiles."""
    op.add_column(
        'student_profiles',
        sa.Column('retake_semesters', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Remove retake_semesters column from student_profiles."""
    op.drop_column('student_profiles', 'retake_semesters')
