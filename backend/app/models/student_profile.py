"""
Student Profile model
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
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
    weekly_study_goal = Column(Float, nullable=False)  # hours
    preferences = Column(JSON, nullable=True)  # max 5000 chars when serialized
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<StudentProfile(id={self.id}, user_id={self.user_id}, cursus='{self.cursus}')>"
