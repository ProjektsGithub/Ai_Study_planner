"""fix_unique_constraints_soft_delete

Fixes unique constraints to allow duplicate names for soft-deleted records.
This enables the reset functionality to work properly - after soft-deleting
entities, users can import new entities with the same names.

Changes:
- Removes simple unique constraints on name fields
- Adds partial unique indexes that only apply when is_deleted=False
- Applies to: universities, study_programs, campuses, academic_tracks

Revision ID: e8a9c7f3d512
Revises: c91e34f7b201
Create Date: 2026-06-24 18:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'e8a9c7f3d512'
down_revision: Union[str, Sequence[str], None] = 'c91e34f7b201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace simple unique constraints with partial unique indexes.
    
    PostgreSQL partial indexes allow us to enforce uniqueness only for
    records where is_deleted=FALSE, so soft-deleted records don't
    conflict with new records having the same name.
    """
    
    # 1. UNIVERSITIES - Drop unique constraint, add partial unique index
    op.execute("""
        -- Drop existing unique constraint and index
        ALTER TABLE universities DROP CONSTRAINT IF EXISTS universities_name_key;
        DROP INDEX IF EXISTS ix_universities_name;
        
        -- Create partial unique index (only for non-deleted records)
        CREATE UNIQUE INDEX ix_universities_name_unique_active
        ON universities (name)
        WHERE is_deleted = FALSE;
        
        -- Create regular index for lookups (includes deleted records)
        CREATE INDEX ix_universities_name
        ON universities (name);
    """)
    
    # 2. STUDY_PROGRAMS - Drop unique constraint, add partial unique index
    op.execute("""
        -- Drop existing unique constraint if it exists
        ALTER TABLE study_programs DROP CONSTRAINT IF EXISTS study_programs_name_key;
        DROP INDEX IF EXISTS ix_study_programs_name;
        
        -- Create partial unique index (only for non-deleted records)
        CREATE UNIQUE INDEX ix_study_programs_name_unique_active
        ON study_programs (name)
        WHERE is_deleted = FALSE;
        
        -- Create regular index for lookups
        CREATE INDEX ix_study_programs_name
        ON study_programs (name);
    """)
    
    # 3. CAMPUSES - Create partial unique index on (university_id, name)
    # Campuses should be unique per university when not deleted
    op.execute("""
        -- Drop existing constraints if any
        DROP INDEX IF EXISTS ix_campuses_name;
        
        -- Create partial unique index (university + name, only active)
        CREATE UNIQUE INDEX ix_campuses_university_name_unique_active
        ON campuses (university_id, name)
        WHERE is_deleted = FALSE;
        
        -- Create regular index for lookups
        CREATE INDEX ix_campuses_name
        ON campuses (name);
    """)
    
    # 4. ACADEMIC_TRACKS - Create partial unique index on (study_program_id, name)
    # Tracks should be unique per program when not deleted
    op.execute("""
        -- Drop existing constraints if any
        DROP INDEX IF EXISTS ix_academic_tracks_name;
        
        -- Create partial unique index (program + name, only active)
        CREATE UNIQUE INDEX ix_academic_tracks_program_name_unique_active
        ON academic_tracks (study_program_id, name)
        WHERE is_deleted = FALSE;
        
        -- Create regular index for lookups
        CREATE INDEX ix_academic_tracks_name
        ON academic_tracks (name);
    """)
    
    # 5. COURSES - Create partial unique index on (semester_id, code)
    # Course codes should be unique per semester when not deleted
    op.execute("""
        -- Drop existing constraints if any
        DROP INDEX IF EXISTS ix_courses_code;
        
        -- Create partial unique index (semester + code, only active)
        CREATE UNIQUE INDEX ix_courses_semester_code_unique_active
        ON courses (semester_id, code)
        WHERE is_deleted = FALSE;
        
        -- Create regular index for lookups
        CREATE INDEX ix_courses_code
        ON courses (code);
    """)


def downgrade() -> None:
    """
    Restore simple unique constraints (may fail if soft-deleted duplicates exist).
    """
    
    # Restore universities
    op.execute("""
        DROP INDEX IF EXISTS ix_universities_name_unique_active;
        DROP INDEX IF EXISTS ix_universities_name;
        CREATE UNIQUE INDEX ix_universities_name ON universities (name);
    """)
    
    # Restore study_programs
    op.execute("""
        DROP INDEX IF EXISTS ix_study_programs_name_unique_active;
        DROP INDEX IF EXISTS ix_study_programs_name;
        CREATE UNIQUE INDEX ix_study_programs_name ON study_programs (name);
    """)
    
    # Restore campuses
    op.execute("""
        DROP INDEX IF EXISTS ix_campuses_university_name_unique_active;
        DROP INDEX IF EXISTS ix_campuses_name;
        CREATE INDEX ix_campuses_name ON campuses (name);
    """)
    
    # Restore academic_tracks
    op.execute("""
        DROP INDEX IF EXISTS ix_academic_tracks_program_name_unique_active;
        DROP INDEX IF EXISTS ix_academic_tracks_name;
        CREATE INDEX ix_academic_tracks_name ON academic_tracks (name);
    """)
    
    # Restore courses
    op.execute("""
        DROP INDEX IF EXISTS ix_courses_semester_code_unique_active;
        DROP INDEX IF EXISTS ix_courses_code;
        CREATE INDEX ix_courses_code ON courses (code);
    """)

