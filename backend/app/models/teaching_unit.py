"""
Teaching Unit model for grouping related courses (UE - Unité d'Enseignement)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class TeachingUnit(Base):
    """Teaching Unit model representing a grouping of related courses"""
    
    __tablename__ = "teaching_units"
    
    id = Column(Integer, primary_key=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name
    code = Column(String(50), nullable=True, unique=True, index=True)  # UE code (e.g., UE1, UE2)
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # ECTS requirements for this teaching unit
    ects_required = Column(Integer, nullable=True)
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    semester = relationship("Semester", back_populates="teaching_units")
    courses = relationship("Course", back_populates="teaching_unit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TeachingUnit(id={self.id}, name='{self.name}', code='{self.code}')>"
