"""
Student Profile model
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class StudentProfile(Base):
    """Student profile with academic information and preferences"""
    
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cursus = Column(String(100), nullable=False)
    academic_level = Column(String(50), nullable=False)
    weekly_study_goal = Column(Float, nullable=False)
    
    semester_start_date = Column(Date, nullable=True)
    semester_end_date = Column(Date, nullable=True)
    exam_period_start = Column(Date, nullable=True)
    
    total_course_hours_per_week = Column(Float, nullable=True)
    other_commitments_hours = Column(Float, nullable=True)
    
    preferred_study_time = Column(String(20), nullable=True)
    preferred_session_duration = Column(Integer, nullable=True)
    study_pace = Column(String(20), nullable=True)
    
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<StudentProfile(id={self.id}, user_id={self.user_id}, cursus='{self.cursus}')>"
