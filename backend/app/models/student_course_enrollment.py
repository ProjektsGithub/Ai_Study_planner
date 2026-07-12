"""
StudentCourseEnrollment model
Links a student to a course from the admin catalog with a status and optional notes.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class StudentCourseEnrollment(Base):
    """
    Represents a student's enrollment in a catalog course with a qualification status.

    Status values and their meaning for the AI planner:
    - in_progress : active course — include normally in the schedule
    - validated   : already passed — exclude from schedule (free up time)
    - retake      : failed / needs retry — HIGH priority in schedule
    - optional    : elective — include only if spare time available
    """

    __tablename__ = "student_course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status used by the AI planner
    status = Column(
        String(20),
        nullable=False,
        default="in_progress",
        index=True,
    )  # in_progress | validated | retake | optional

    # Optional: student can override the catalog priority (1-5)
    priority_override = Column(Integer, nullable=True)

    # Free-text notes visible only to the student
    personal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Each student can enroll in a course only once
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_student_course"),
    )

    # Relationships
    user = relationship("User", back_populates="course_enrollments")
    course = relationship("Course")

    def __repr__(self):
        return (
            f"<StudentCourseEnrollment(user={self.user_id}, "
            f"course={self.course_id}, status='{self.status}')>"
        )
