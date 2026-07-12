"""
Admin Permission model for fine-grained access control
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class AdminPermission(Base):
    """Permission assignment for admin roles"""
    
    __tablename__ = "admin_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("admin_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., 'university', 'course', 'program'
    action = Column(String(50), nullable=False, index=True)  # e.g., 'create', 'read', 'update', 'delete', 'manage'
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    role = relationship("AdminRole", back_populates="permissions")
    
    def __repr__(self):
        return f"<AdminPermission(id={self.id}, role_id={self.role_id}, resource='{self.resource}', action='{self.action}')>"
