"""
User Role assignment model for linking users to admin roles with scope
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class UserRole(Base):
    """User role assignment with optional university and program scope"""
    
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("admin_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    university_id = Column(Integer, nullable=True, index=True)  # Null for super_admin, specific ID for university_admin
    program_id = Column(Integer, nullable=True, index=True)  # Null for super_admin and university_admin, specific ID for program_coordinator
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # User who assigned this role
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("AdminRole", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id}, university_id={self.university_id}, program_id={self.program_id})>"
