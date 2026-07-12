"""
Course Prerequisite model for prerequisite relationship management
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Table
from datetime import datetime, timezone
from app.core.database import Base


class CoursePrerequisite(Base):
    """
    Course Prerequisite model representing prerequisite relationships between courses.
    Defines that prerequisite_id must be completed before course_id.
    """
    
    __tablename__ = "course_prerequisites"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<CoursePrerequisite(course_id={self.course_id}, prerequisite_id={self.prerequisite_id})>"
