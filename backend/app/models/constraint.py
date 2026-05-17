"""
Constraint model
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Constraint(Base):
    """Scheduling constraints (forbidden slots, max hours, breaks, fixed slots)"""
    
    __tablename__ = "constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_type = Column(String(50), nullable=False)  # forbidden_slot, max_daily_hours, required_break, fixed_slot
    parameters = Column(JSON, nullable=False)  # Type-specific parameters
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="constraints")
    
    def __repr__(self):
        return f"<Constraint(id={self.id}, type='{self.constraint_type}', active={self.active})>"
