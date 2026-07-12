"""
Subject model
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Subject(Base):
    """Academic subject with priority, difficulty, and exam date"""
    
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)
    target_weekly_hours = Column(Float, nullable=False)
    exam_date = Column(Date, nullable=True)
    
    exam_type = Column(String(30), nullable=True)
    ects_credits = Column(Float, nullable=True)
    coefficient = Column(Float, nullable=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    validation_status = Column(String(20), default="in_progress", nullable=False)
    
    weekly_class_hours = Column(Float, nullable=True)
    current_progress = Column(Float, default=0.0, nullable=False)
    weak_topics = Column(JSON, nullable=True)

    # Link to admin catalogue course (set when created via enrollment sync)
    catalog_course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user = relationship("User", back_populates="subjects")
    study_sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', priority={self.priority})>"
