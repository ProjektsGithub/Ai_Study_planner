"""Add enhanced student fields

Revision ID: a8f2e3b4c567
Revises: 4c065a15bc77
Create Date: 2026-06-04 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8f2e3b4c567'
down_revision: Union[str, Sequence[str], None] = '4c065a15bc77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced fields to student_profiles, subjects, and availabilities"""
    
    op.add_column('student_profiles', sa.Column('semester_start_date', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('semester_end_date', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('exam_period_start', sa.Date(), nullable=True))
    op.add_column('student_profiles', sa.Column('total_course_hours_per_week', sa.Float(), nullable=True))
    op.add_column('student_profiles', sa.Column('other_commitments_hours', sa.Float(), nullable=True))
    op.add_column('student_profiles', sa.Column('preferred_study_time', sa.String(length=20), nullable=True))
    op.add_column('student_profiles', sa.Column('preferred_session_duration', sa.Integer(), nullable=True))
    op.add_column('student_profiles', sa.Column('study_pace', sa.String(length=20), nullable=True))
    
    op.add_column('subjects', sa.Column('exam_type', sa.String(length=30), nullable=True))
    op.add_column('subjects', sa.Column('ects_credits', sa.Float(), nullable=True))
    op.add_column('subjects', sa.Column('coefficient', sa.Float(), nullable=True))
    op.add_column('subjects', sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('subjects', sa.Column('validation_status', sa.String(length=20), nullable=False, server_default='in_progress'))
    op.add_column('subjects', sa.Column('weekly_class_hours', sa.Float(), nullable=True))
    op.add_column('subjects', sa.Column('current_progress', sa.Float(), nullable=False, server_default='0'))
    op.add_column('subjects', sa.Column('weak_topics', sa.JSON(), nullable=True))
    
    op.add_column('availabilities', sa.Column('energy_level', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Remove enhanced fields"""
    
    op.drop_column('availabilities', 'energy_level')
    
    op.drop_column('subjects', 'weak_topics')
    op.drop_column('subjects', 'current_progress')
    op.drop_column('subjects', 'weekly_class_hours')
    op.drop_column('subjects', 'validation_status')
    op.drop_column('subjects', 'is_mandatory')
    op.drop_column('subjects', 'coefficient')
    op.drop_column('subjects', 'ects_credits')
    op.drop_column('subjects', 'exam_type')
    
    op.drop_column('student_profiles', 'study_pace')
    op.drop_column('student_profiles', 'preferred_session_duration')
    op.drop_column('student_profiles', 'preferred_study_time')
    op.drop_column('student_profiles', 'other_commitments_hours')
    op.drop_column('student_profiles', 'total_course_hours_per_week')
    op.drop_column('student_profiles', 'exam_period_start')
    op.drop_column('student_profiles', 'semester_end_date')
    op.drop_column('student_profiles', 'semester_start_date')
