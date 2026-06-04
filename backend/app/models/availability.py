"""
Availability model
"""
from sqlalchemy import Column, Integer, String, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Availability(Base):
    """Weekly availability time slots"""
    
    __tablename__ = "availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    energy_level = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user = relationship("User", back_populates="availabilities")
    
    def __repr__(self):
        return f"<Availability(id={self.id}, day='{self.day_of_week}', {self.start_time}-{self.end_time})>"
