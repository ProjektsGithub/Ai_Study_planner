"""
Prerequisite relationship model with circular dependency prevention
"""
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone
from app.core.database import Base


class Prerequisite(Base):
    """Prerequisite relationship model linking courses with their prerequisites"""
    
    __tablename__ = "prerequisites"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)  # Whether prerequisite is mandatory or recommended
    description = Column(String(500), nullable=True)  # Optional description of prerequisite requirement
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # User who created relationship
    
    # Relationships
    course = relationship("Course", foreign_keys=[course_id], back_populates="prerequisite_for")
    prerequisite_course = relationship("Course", foreign_keys=[prerequisite_course_id], back_populates="required_by")
    
    @validates('course_id', 'prerequisite_course_id')
    def validate_course_ids(self, key, value):
        """Validate that course IDs are valid"""
        if value is None:
            raise ValueError(f"{key} cannot be null")
        if value < 1:
            raise ValueError(f"{key} must be a positive integer")
        return value
    
    def __repr__(self):
        return f"<Prerequisite(id={self.id}, course_id={self.course_id}, prerequisite_course_id={self.prerequisite_course_id})>"
