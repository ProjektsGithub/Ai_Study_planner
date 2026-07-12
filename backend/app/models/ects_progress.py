"""
ECTSProgress model — cached ECTS progression snapshot per student.

One row per user (unique constraint on user_id).
Recalculated whenever a course grade changes to 'validated'.
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ECTSProgress(Base):
    """
    Stores the computed ECTS progression for a student.

    Fields:
        ects_obtained         — sum of ECTS from all validated courses
        ects_required         — total ECTS required for graduation (from Super Admin Platform)
        ects_remaining        — ects_required - ects_obtained
        progression_percentage— (ects_obtained / ects_required) * 100, 2 decimal precision
        last_calculated_at    — timestamp of last recalculation
    """

    __tablename__ = "ects_progress"

    id = Column(Integer, primary_key=True, index=True)

    # Unique: one ECTS record per student
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    ects_obtained = Column(Float, nullable=False, default=0.0)
    ects_required = Column(Float, nullable=False)
    ects_remaining = Column(Float, nullable=False)
    progression_percentage = Column(Float, nullable=False)

    last_calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="ects_progress")

    def __repr__(self):
        return (
            f"<ECTSProgress(user_id={self.user_id}, "
            f"obtained={self.ects_obtained}, required={self.ects_required}, "
            f"progression={self.progression_percentage:.2f}%)>"
        )
