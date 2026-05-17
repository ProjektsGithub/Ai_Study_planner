"""
Generation Log model
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class GenerationLog(Base):
    """Log of AI service generation requests"""
    
    __tablename__ = "generation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    duration_seconds = Column(Float, nullable=False)
    token_count = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="generation_logs")
    
    def __repr__(self):
        return f"<GenerationLog(id={self.id}, success={self.success}, duration={self.duration_seconds}s)>"
