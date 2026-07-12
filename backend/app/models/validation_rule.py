"""
Validation Rule model for academic progression requirements
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum
from app.core.database import Base


class RuleType(str, Enum):
    """Enum for validation rule types"""
    SEMESTER_VALIDATION = "semester_validation"
    YEAR_PROGRESSION = "year_progression"
    GRADUATION = "graduation"


class ValidationRule(Base):
    """Validation Rule model for defining ECTS requirements and progression criteria"""
    
    __tablename__ = "validation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    academic_track_id = Column(Integer, ForeignKey("academic_tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(SQLEnum(RuleType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    name_de = Column(String(255), nullable=True)  # German name
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # ECTS requirement
    minimum_ects = Column(Integer, nullable=False)
    
    # Additional conditions (stored as text, can be parsed or displayed)
    additional_conditions = Column(Text, nullable=True)
    additional_conditions_de = Column(Text, nullable=True)  # German conditions
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    academic_track = relationship("AcademicTrack", back_populates="validation_rules")
    
    def __repr__(self):
        return f"<ValidationRule(id={self.id}, rule_type='{self.rule_type}', minimum_ects={self.minimum_ects})>"
