"""
Academic Track model for managing degree levels (Cursus)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum
from app.core.database import Base


class TrackLevel(str, Enum):
    """Enum for academic track levels"""
    BACHELOR = "bachelor"  # Licence
    MASTER = "master"
    DOCTORATE = "doctorate"  # Doctorat


class AcademicTrack(Base):
    """Academic Track model representing a degree level (Bachelor, Master, Doctorate)"""
    
    __tablename__ = "academic_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    study_program_id = Column(Integer, ForeignKey("study_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name
    level = Column(SQLEnum(TrackLevel), nullable=False, index=True)
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # ECTS requirements
    total_ects_required = Column(Integer, nullable=False)  # Total ECTS for graduation
    
    # Graduation conditions
    graduation_conditions = Column(Text, nullable=True)
    graduation_conditions_de = Column(Text, nullable=True)  # German graduation conditions
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    study_program = relationship("StudyProgram", back_populates="academic_tracks")
    semesters = relationship("Semester", back_populates="academic_track", cascade="all, delete-orphan")
    validation_rules = relationship("ValidationRule", back_populates="academic_track", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AcademicTrack(id={self.id}, name='{self.name}', level='{self.level}', total_ects={self.total_ects_required})>"
