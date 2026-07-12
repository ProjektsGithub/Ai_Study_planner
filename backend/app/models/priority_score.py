"""
PriorityScore model — per-course priority score with recommended study hours.
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class PriorityScore(Base):
    """
    Stores the calculated priority score for a student's course.

    priority_score: 0.0–100.0 (higher = more urgent to study)
    recommended_weekly_hours: suggested hours/week based on priority
    success_probability: 0.0–100.0 estimated chance of passing
    factors: JSON dict with the weighted breakdown used in calculation
    """

    __tablename__ = "priority_scores"

    id = Column(Integer, primary_key=True, index=True)

    # FK to users with CASCADE delete
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Course reference (ID from Super Admin Platform — courses table)
    course_id = Column(Integer, nullable=False, index=True)

    # Score from 0.0 to 100.0
    priority_score = Column(Float, nullable=False)

    # Recommended hours per week for this course
    recommended_weekly_hours = Column(Float, nullable=True)

    # Estimated probability of passing 0.0–100.0
    success_probability = Column(Float, nullable=True)

    # JSON breakdown: ects_contribution, coefficient_contribution, exam_proximity, etc.
    factors = Column(JSON, nullable=True)

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="priority_scores")

    # Composite indexes
    __table_args__ = (
        Index("idx_user_priority", "user_id", "priority_score"),
    )

    def __repr__(self):
        return (
            f"<PriorityScore(id={self.id}, user_id={self.user_id}, "
            f"course_id={self.course_id}, score={self.priority_score:.1f})>"
        )
