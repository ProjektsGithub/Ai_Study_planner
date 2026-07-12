"""
Exam model — stores exam schedule entries with date, time, location, and weight.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Time, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Exam(Base):
    """
    Tracks an exam for a student's course.

    exam_type values: midterm | final | practical | oral | project
    weight: 0.0–1.0 representing percentage of final grade (e.g. 0.6 = 60%)
    """

    __tablename__ = "exams"

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

    # Exam scheduling
    exam_date = Column(Date, nullable=False, index=True)
    exam_time = Column(Time, nullable=True)
    location = Column(String(200), nullable=True)

    # midterm | final | practical | oral | project
    exam_type = Column(String(50), nullable=True)

    # Importance factor 0.0–1.0 (e.g. 0.4 = 40% of final grade)
    weight = Column(Float, nullable=False, default=1.0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="exams")

    # Composite indexes
    __table_args__ = (
        Index("idx_user_exam_date", "user_id", "exam_date"),
    )

    def __repr__(self):
        return (
            f"<Exam(id={self.id}, user_id={self.user_id}, "
            f"course_id={self.course_id}, exam_date={self.exam_date}, "
            f"type='{self.exam_type}')>"
        )
