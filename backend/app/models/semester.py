"""
Semester model for academic period management
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Semester(Base):
    """Semester model representing an academic period within an academic track"""
    
    __tablename__ = "semesters"
    
    id = Column(Integer, primary_key=True, index=True)
    academic_track_id = Column(Integer, ForeignKey("academic_tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)  # e.g., "S1", "S2", "S3"
    name_de = Column(String(100), nullable=True)  # German name
    semester_number = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5, 6 (Bachelor: 1-6, Master: 1-4)
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # ECTS requirements for this semester
    ects_required = Column(Integer, nullable=True)
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    academic_track = relationship("AcademicTrack", back_populates="semesters")
    teaching_units = relationship("TeachingUnit", back_populates="semester", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="semester", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Semester(id={self.id}, name='{self.name}', semester_number={self.semester_number}, track_id={self.academic_track_id})>"
