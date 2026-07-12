"""
University model for managing academic institutions
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class University(Base):
    """University model representing an academic institution"""
    
    __tablename__ = "universities"
    
    id = Column(Integer, primary_key=True, index=True)
    # Note: Uniqueness enforced by partial index ix_universities_name_unique_active (WHERE is_deleted = FALSE)
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name
    country = Column(String(100), nullable=False, default="Germany")
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    campuses = relationship("Campus", back_populates="university", cascade="all, delete-orphan")
    study_programs = relationship("StudyProgram", secondary="university_programs", back_populates="universities")
    
    def __repr__(self):
        return f"<University(id={self.id}, name='{self.name}', country='{self.country}')>"
