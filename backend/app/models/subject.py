"""
Subject model
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Subject(Base):
    """Academic subject with priority, difficulty, and exam date"""
    
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False)  # 1-5 scale
    difficulty = Column(Integer, nullable=False)  # 1-5 scale
    target_weekly_hours = Column(Float, nullable=False)  # 0.5-168 range
    exam_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subjects")
    study_sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', priority={self.priority})>"
