"""
Grade model — stores grade obtained per course attempt with validation status.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Grade(Base):
    """
    Records a student's grade for a specific course attempt.

    validation_status:
        - 'in_progress' — no grade entered yet
        - 'validated'   — grade_obtained >= min_passing_grade
        - 'failed'      — grade_obtained < min_passing_grade
    """

    __tablename__ = "grades"

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
    course_name = Column(String(200), nullable=False)

    # Grade data
    grade_obtained = Column(Float, nullable=True)       # None => in_progress
    min_passing_grade = Column(Float, nullable=False)   # e.g. 10.0 on /20
    max_grade = Column(Float, nullable=False, default=20.0)

    # Calculated automatically: validated | failed | in_progress
    validation_status = Column(String(20), nullable=False, index=True)

    attempt_number = Column(Integer, nullable=False, default=1)
    semester = Column(Integer, nullable=True)

    # From Super Admin Platform course record
    ects_credits = Column(Float, nullable=True)
    coefficient = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("User", back_populates="grades")

    # Composite indexes
    __table_args__ = (
        Index("idx_user_course", "user_id", "course_id"),
        Index("idx_validation_status", "validation_status"),
    )

    def __repr__(self):
        return (
            f"<Grade(id={self.id}, user_id={self.user_id}, "
            f"course_id={self.course_id}, status='{self.validation_status}', "
            f"attempt={self.attempt_number})>"
        )
