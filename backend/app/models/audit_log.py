"""
Audit Log model for tracking administrative changes
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all administrative operations"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., 'university', 'course', 'program'
    entity_id = Column(Integer, nullable=False, index=True)
    operation = Column(String(20), nullable=False, index=True)  # 'create', 'update', 'delete'
    before_value = Column(JSON, nullable=True)  # State before the operation
    after_value = Column(JSON, nullable=True)  # State after the operation
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    description = Column(Text, nullable=True)  # Optional human-readable description
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, operation='{self.operation}')>"
