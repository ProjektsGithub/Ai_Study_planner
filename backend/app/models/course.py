"""
Course model for managing individual subjects/courses
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


# Association table for course prerequisites (many-to-many self-referential)
course_prerequisites = Table(
    'course_prerequisites',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('prerequisite_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
)


class Course(Base):
    """Course model representing a specific subject with ECTS, coefficient, and difficulty"""
    
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    teaching_unit_id = Column(Integer, ForeignKey("teaching_units.id", ondelete="CASCADE"), nullable=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name
    # Note: Code uniqueness enforced by partial index ix_courses_semester_code_unique_active (WHERE is_deleted = FALSE)
    code = Column(String(50), nullable=True, index=True)  # Course code (e.g., CS101, MATH201)
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # Course properties
    ects_credits = Column(Integer, nullable=False)  # ECTS credits (1-30)
    coefficient = Column(Float, nullable=False)  # Weight in grade calculations (0.1-10.0)
    difficulty_level = Column(Integer, nullable=False)  # Difficulty level (1-5)
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    teaching_unit = relationship("TeachingUnit", back_populates="courses")
    semester = relationship("Semester", back_populates="courses")
    
    # Self-referential many-to-many for prerequisites
    prerequisites = relationship(
        "Course",
        secondary=course_prerequisites,
        primaryjoin=id == course_prerequisites.c.course_id,
        secondaryjoin=id == course_prerequisites.c.prerequisite_id,
        backref="dependent_courses"
    )
    
    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}', code='{self.code}', ects={self.ects_credits})>"
