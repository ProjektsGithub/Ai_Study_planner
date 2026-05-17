"""
Study Plan model
"""
from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class StudyPlan(Base):
    """Weekly study plan with sessions"""
    
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # generated, superseded, outdated
    summary = Column(Text, nullable=True)
    edited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    sessions = relationship("StudySession", back_populates="study_plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<StudyPlan(id={self.id}, plan_id='{self.plan_id}', week_start={self.week_start}, status='{self.status}')>"
