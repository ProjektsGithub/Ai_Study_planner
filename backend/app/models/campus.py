"""
Campus model for university campus locations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Campus(Base):
    """Campus model representing a physical location of a university"""
    
    __tablename__ = "campuses"
    
    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_de = Column(String(255), nullable=True)  # German name
    location = Column(String(255), nullable=True)  # City or address
    description = Column(Text, nullable=True)
    description_de = Column(Text, nullable=True)  # German description
    
    # Soft delete fields for audit trail
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    university = relationship("University", back_populates="campuses")
    
    def __repr__(self):
        return f"<Campus(id={self.id}, name='{self.name}', university_id={self.university_id})>"
