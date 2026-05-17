"""
Study Session model
"""
from sqlalchemy import Column, Integer, String, Time, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudySession(Base):
    """Individual study session within a study plan"""
    
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    day = Column(String(10), nullable=False)  # Monday-Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    task_type = Column(String(20), nullable=False)  # revision, exercises, reading, project, exam_prep
    notes = Column(Text, nullable=True)
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="sessions")
    subject = relationship("Subject", back_populates="study_sessions")
    
    def __repr__(self):
        return f"<StudySession(id={self.id}, day='{self.day}', {self.start_time}-{self.end_time})>"
