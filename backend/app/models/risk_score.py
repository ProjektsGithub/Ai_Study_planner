"""
RiskScore model — per-course academic risk level with contributing factors.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RiskScore(Base):
    """
    Stores the calculated academic risk level for a student's course.

    risk_level values: low | medium | high
    factors: JSON dict with the contributing factors used in calculation,
             e.g. {"validation_status": "failed", "days_until_exam": 5, ...}
    """

    __tablename__ = "risk_scores"

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

    # low | medium | high
    risk_level = Column(String(20), nullable=False, index=True)

    # JSON breakdown of factors that contributed to this risk level
    factors = Column(JSON, nullable=True)

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="risk_scores")

    # Composite indexes
    __table_args__ = (
        Index("idx_user_course_risk", "user_id", "course_id", "risk_level"),
    )

    def __repr__(self):
        return (
            f"<RiskScore(id={self.id}, user_id={self.user_id}, "
            f"course_id={self.course_id}, risk_level='{self.risk_level}')>"
        )
