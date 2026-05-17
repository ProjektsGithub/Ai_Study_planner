"""Initial database schema

Revision ID: 4c065a15bc77
Revises: 
Create Date: 2026-05-17 02:37:30.265696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c065a15bc77'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('last_failed_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create student_profiles table
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cursus', sa.String(length=100), nullable=False),
        sa.Column('academic_level', sa.String(length=50), nullable=False),
        sa.Column('weekly_study_goal', sa.Float(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_student_profiles_id'), 'student_profiles', ['id'], unique=False)
    
    # Create subjects table
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('target_weekly_hours', sa.Float(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subjects_id'), 'subjects', ['id'], unique=False)
    op.create_index(op.f('ix_subjects_user_id'), 'subjects', ['user_id'], unique=False)
    
    # Create availabilities table
    op.create_table(
        'availabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.String(length=10), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_availabilities_id'), 'availabilities', ['id'], unique=False)
    op.create_index(op.f('ix_availabilities_user_id'), 'availabilities', ['user_id'], unique=False)
    
    # Create constraints table
    op.create_table(
        'constraints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('constraint_type', sa.String(length=50), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_constraints_id'), 'constraints', ['id'], unique=False)
    op.create_index(op.f('ix_constraints_user_id_active'), 'constraints', ['user_id', 'active'], unique=False)
    
    # Create study_plans table
    op.create_table(
        'study_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('edited', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_plans_id'), 'study_plans', ['id'], unique=False)
    op.create_index(op.f('ix_study_plans_plan_id'), 'study_plans', ['plan_id'], unique=True)
    op.create_index(op.f('ix_study_plans_user_id'), 'study_plans', ['user_id'], unique=False)
    op.create_index(op.f('ix_study_plans_week_start'), 'study_plans', ['week_start'], unique=False)
    op.create_index(op.f('ix_study_plans_status'), 'study_plans', ['status'], unique=False)
    
    # Create study_sessions table
    op.create_table(
        'study_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('study_plan_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('day', sa.String(length=10), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('task_type', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['study_plan_id'], ['study_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_sessions_id'), 'study_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_study_sessions_study_plan_id'), 'study_sessions', ['study_plan_id'], unique=False)
    
    # Create generation_logs table
    op.create_table(
        'generation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generation_logs_id'), 'generation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_generation_logs_user_id'), 'generation_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_generation_logs_request_hash'), 'generation_logs', ['request_hash'], unique=False)
    op.create_index(op.f('ix_generation_logs_success'), 'generation_logs', ['success'], unique=False)
    op.create_index(op.f('ix_generation_logs_created_at'), 'generation_logs', ['created_at'], unique=False)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(length=1000), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_read'), 'notifications', ['read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_generation_logs_created_at'), table_name='generation_logs')
    op.drop_index(op.f('ix_generation_logs_success'), table_name='generation_logs')
    op.drop_index(op.f('ix_generation_logs_request_hash'), table_name='generation_logs')
    op.drop_index(op.f('ix_generation_logs_user_id'), table_name='generation_logs')
    op.drop_index(op.f('ix_generation_logs_id'), table_name='generation_logs')
    op.drop_table('generation_logs')
    
    op.drop_index(op.f('ix_study_sessions_study_plan_id'), table_name='study_sessions')
    op.drop_index(op.f('ix_study_sessions_id'), table_name='study_sessions')
    op.drop_table('study_sessions')
    
    op.drop_index(op.f('ix_study_plans_status'), table_name='study_plans')
    op.drop_index(op.f('ix_study_plans_week_start'), table_name='study_plans')
    op.drop_index(op.f('ix_study_plans_user_id'), table_name='study_plans')
    op.drop_index(op.f('ix_study_plans_plan_id'), table_name='study_plans')
    op.drop_index(op.f('ix_study_plans_id'), table_name='study_plans')
    op.drop_table('study_plans')
    
    op.drop_index(op.f('ix_constraints_user_id_active'), table_name='constraints')
    op.drop_index(op.f('ix_constraints_id'), table_name='constraints')
    op.drop_table('constraints')
    
    op.drop_index(op.f('ix_availabilities_user_id'), table_name='availabilities')
    op.drop_index(op.f('ix_availabilities_id'), table_name='availabilities')
    op.drop_table('availabilities')
    
    op.drop_index(op.f('ix_subjects_user_id'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_id'), table_name='subjects')
    op.drop_table('subjects')
    
    op.drop_index(op.f('ix_student_profiles_id'), table_name='student_profiles')
    op.drop_table('student_profiles')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
