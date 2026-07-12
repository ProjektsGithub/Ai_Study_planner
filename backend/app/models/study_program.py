"""
Study Program model for managing fields of study (Filière)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


# Association table for many-to-many relationship between universities and study programs
university_programs = Table(
    'university_programs',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('university_id', Integer, ForeignKey('universities.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('study_program_id', Integer, ForeignKey('study_programs.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
)


class StudyProgram(Base):
    """Study Program model representing a field of study (e.g., Computer Science, Medicine, Law)"""
    
    __tablename__ = "study_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    # Note: Uniqueness enforced by partial index ix_study_programs_name_unique_active (WHERE is_deleted = FALSE)
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name (primary language)
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    # Note: Code uniqueness enforced by partial index (WHERE is_deleted = FALSE)
    code = Column(String(50), nullable=True, index=True)  # Program code (e.g., CS, MED, LAW)
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    universities = relationship("University", secondary=university_programs, back_populates="study_programs")
    academic_tracks = relationship("AcademicTrack", back_populates="study_program", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<StudyProgram(id={self.id}, name='{self.name}', code='{self.code}')>"
