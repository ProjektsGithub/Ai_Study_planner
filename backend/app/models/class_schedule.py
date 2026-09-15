"""
Class Schedule model for managing university class timetables (Emploi du temps)
"""
from sqlalchemy import Column, Integer, String, Time, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class ClassSchedule(Base):
    """
    Represents a fixed university class/lecture slot for a specific program, track, and semester.
    Types: CM (Cours Magistral), TD (Travaux Dirigés), TP (Travaux Pratiques), EXAM.
    """

    __tablename__ = "class_schedules"

    id = Column(Integer, primary_key=True, index=True)

    # Academic hierarchy foreign keys
    study_program_id = Column(Integer, ForeignKey("study_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_track_id = Column(Integer, ForeignKey("academic_tracks.id", ondelete="CASCADE"), nullable=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)

    # Class details
    course_name = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=True)
    day_of_week = Column(String(10), nullable=False, index=True)  # Monday - Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    session_type = Column(String(20), nullable=False, default="CM")  # CM, TD, TP, EXAM
    group_name = Column(String(50), nullable=True)  # e.g., "Gruppe 1", "Groupe A", or None
    room_location = Column(String(100), nullable=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    is_fixed = Column(Boolean, default=True, nullable=False)  # True for fixed CM, False for flexible TD/TP

    # Audit & timestamps
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    study_program = relationship("StudyProgram")
    academic_track = relationship("AcademicTrack")
    semester = relationship("Semester")
    course = relationship("Course")

    def __repr__(self):
        return f"<ClassSchedule(id={self.id}, course='{self.course_name}', day='{self.day_of_week}', {self.start_time}-{self.end_time}, type='{self.session_type}')>"
