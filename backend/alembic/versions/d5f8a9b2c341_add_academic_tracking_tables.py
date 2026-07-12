"""add_academic_tracking_tables

Extends the database schema for the Student Backend Evolution:

1. Extends student_profiles with academic linking fields:
   - university_id, filiere_id, cursus_id (link to Super Admin Platform)
   - current_semester, academic_year

2. Creates new tables:
   - grades           : stores grade per course attempt with validation status
   - exams            : exam schedule with date/time/location/weight
   - ects_progress    : cached ECTS progression snapshot per student
   - risk_scores      : per-course academic risk level with contributing factors
   - priority_scores  : per-course priority score with recommended hours

3. Adds indexes for performance:
   - idx_user_course on grades (user_id, course_id)
   - idx_validation_status on grades
   - idx_user_exam_date on exams (user_id, exam_date)
   - idx_user_course_risk on risk_scores (user_id, course_id, risk_level)
   - idx_user_priority on priority_scores (user_id, priority_score)

All foreign keys reference users.id with CASCADE DELETE.
All new student_profiles columns are nullable for backward compatibility.

Revision ID: d5f8a9b2c341
Revises: c91e34f7b201
Create Date: 2026-06-20 23:30:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op


# revision identifiers
revision: str = 'd5f8a9b2c341'
down_revision: Union[str, Sequence[str], None] = 'c91e34f7b201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply academic tracking schema extensions."""

    # -------------------------------------------------------------------------
    # 1. Extend student_profiles with academic linking fields
    # -------------------------------------------------------------------------
    op.add_column(
        'student_profiles',
        sa.Column('university_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'student_profiles',
        sa.Column('filiere_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'student_profiles',
        sa.Column('cursus_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'student_profiles',
        sa.Column('current_semester', sa.Integer(), nullable=True)
    )
    op.add_column(
        'student_profiles',
        sa.Column('academic_year', sa.Integer(), nullable=True)
    )

    # -------------------------------------------------------------------------
    # 2. Create grades table
    # -------------------------------------------------------------------------
    op.create_table(
        'grades',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column('course_id', sa.Integer(), nullable=False, index=True),
        sa.Column('course_name', sa.String(200), nullable=False),

        sa.Column('grade_obtained', sa.Float(), nullable=True),
        sa.Column('min_passing_grade', sa.Float(), nullable=False),
        sa.Column('max_grade', sa.Float(), nullable=False, server_default='20.0'),

        # validated | failed | in_progress
        sa.Column('validation_status', sa.String(20), nullable=False, index=True),

        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('semester', sa.Integer(), nullable=True),

        sa.Column('ects_credits', sa.Float(), nullable=True),
        sa.Column('coefficient', sa.Float(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_user_course', 'grades', ['user_id', 'course_id'])
    op.create_index('idx_validation_status', 'grades', ['validation_status'])

    # -------------------------------------------------------------------------
    # 3. Create exams table
    # -------------------------------------------------------------------------
    op.create_table(
        'exams',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column('course_id', sa.Integer(), nullable=False, index=True),
        sa.Column('course_name', sa.String(200), nullable=False),

        sa.Column('exam_date', sa.Date(), nullable=False, index=True),
        sa.Column('exam_time', sa.Time(), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),

        # midterm | final | practical | oral | project
        sa.Column('exam_type', sa.String(50), nullable=True),

        # importance factor 0.0–1.0
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_user_exam_date', 'exams', ['user_id', 'exam_date'])

    # -------------------------------------------------------------------------
    # 4. Create ects_progress table (one row per user, unique constraint)
    # -------------------------------------------------------------------------
    op.create_table(
        'ects_progress',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
            index=True
        ),
        sa.Column('ects_obtained', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ects_required', sa.Float(), nullable=False),
        sa.Column('ects_remaining', sa.Float(), nullable=False),
        sa.Column('progression_percentage', sa.Float(), nullable=False),
        sa.Column('last_calculated_at', sa.DateTime(), nullable=False),
    )

    # -------------------------------------------------------------------------
    # 5. Create risk_scores table
    # -------------------------------------------------------------------------
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column('course_id', sa.Integer(), nullable=False, index=True),

        # low | medium | high
        sa.Column('risk_level', sa.String(20), nullable=False, index=True),
        sa.Column('factors', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(
        'idx_user_course_risk',
        'risk_scores',
        ['user_id', 'course_id', 'risk_level']
    )

    # -------------------------------------------------------------------------
    # 6. Create priority_scores table
    # -------------------------------------------------------------------------
    op.create_table(
        'priority_scores',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        ),
        sa.Column('course_id', sa.Integer(), nullable=False, index=True),

        # 0.0 – 100.0
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('recommended_weekly_hours', sa.Float(), nullable=True),
        sa.Column('success_probability', sa.Float(), nullable=True),
        sa.Column('factors', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
    )
    op.create_index(
        'idx_user_priority',
        'priority_scores',
        ['user_id', 'priority_score']
    )


def downgrade() -> None:
    """Rollback academic tracking schema extensions."""

    # Drop indexes first, then tables (reverse of creation order)
    op.drop_index('idx_user_priority', table_name='priority_scores')
    op.drop_table('priority_scores')

    op.drop_index('idx_user_course_risk', table_name='risk_scores')
    op.drop_table('risk_scores')

    op.drop_table('ects_progress')

    op.drop_index('idx_user_exam_date', table_name='exams')
    op.drop_table('exams')

    op.drop_index('idx_validation_status', table_name='grades')
    op.drop_index('idx_user_course', table_name='grades')
    op.drop_table('grades')

    # Remove new columns from student_profiles
    op.drop_column('student_profiles', 'academic_year')
    op.drop_column('student_profiles', 'current_semester')
    op.drop_column('student_profiles', 'cursus_id')
    op.drop_column('student_profiles', 'filiere_id')
    op.drop_column('student_profiles', 'university_id')
