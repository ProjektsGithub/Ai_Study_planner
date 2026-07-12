"""
Unit tests for audit logging and role models
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.admin_role import AdminRole
from app.models.admin_permission import AdminPermission
from app.models.user_role import UserRole
from app.core.database import Base, engine


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestAuditLog:
    """Test AuditLog model"""
    
    def test_create_audit_log(self, db_session: Session):
        """Test creating an audit log entry"""
        # Create a test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create audit log entry
        audit_log = AuditLog(
            entity_type="university",
            entity_id=1,
            operation="create",
            before_value=None,
            after_value={"name": "Test University", "country": "Germany"},
            user_id=user.id,
            description="Created new university"
        )
        db_session.add(audit_log)
        db_session.commit()
        
        # Verify
        assert audit_log.id is not None
        assert audit_log.entity_type == "university"
        assert audit_log.entity_id == 1
        assert audit_log.operation == "create"
        assert audit_log.before_value is None
        assert audit_log.after_value["name"] == "Test University"
        assert audit_log.user_id == user.id
        assert audit_log.timestamp is not None
        assert audit_log.user.email == "test@example.com"
    
    def test_audit_log_update_operation(self, db_session: Session):
        """Test audit log for update operation with before/after values"""
        user = User(
            email="admin@example.com",
            password_hash="hashed_password",
            name="Admin User"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create audit log for update
        audit_log = AuditLog(
            entity_type="course",
            entity_id=5,
            operation="update",
            before_value={"name": "Old Course Name", "ects_credits": 5},
            after_value={"name": "New Course Name", "ects_credits": 6},
            user_id=user.id,
            description="Updated course details"
        )
        db_session.add(audit_log)
        db_session.commit()
        
        # Verify
        assert audit_log.operation == "update"
        assert audit_log.before_value["name"] == "Old Course Name"
        assert audit_log.after_value["name"] == "New Course Name"
        assert audit_log.before_value["ects_credits"] == 5
        assert audit_log.after_value["ects_credits"] == 6


class TestAdminRole:
    """Test AdminRole model"""
    
    def test_create_admin_role(self, db_session: Session):
        """Test creating an admin role"""
        role = AdminRole(
            name="super_admin",
            display_name="Super Administrator",
            description="Full system access across all universities",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        
        # Verify
        assert role.id is not None
        assert role.name == "super_admin"
        assert role.display_name == "Super Administrator"
        assert role.is_active is True
        assert role.created_at is not None
        assert role.updated_at is not None
    
    def test_unique_role_name(self, db_session: Session):
        """Test that role names must be unique"""
        role1 = AdminRole(
            name="university_admin",
            display_name="University Admin",
            is_active=True
        )
        db_session.add(role1)
        db_session.commit()
        
        # Try to create another role with same name
        role2 = AdminRole(
            name="university_admin",
            display_name="Another University Admin",
            is_active=True
        )
        db_session.add(role2)
        
        # Should raise integrity error
        with pytest.raises(Exception):
            db_session.commit()


class TestAdminPermission:
    """Test AdminPermission model"""
    
    def test_create_admin_permission(self, db_session: Session):
        """Test creating admin permissions"""
        # Create role first
        role = AdminRole(
            name="program_coordinator",
            display_name="Program Coordinator",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        
        # Create permissions
        permission = AdminPermission(
            role_id=role.id,
            resource="course",
            action="create",
            description="Can create courses",
            is_active=True
        )
        db_session.add(permission)
        db_session.commit()
        
        # Verify
        assert permission.id is not None
        assert permission.role_id == role.id
        assert permission.resource == "course"
        assert permission.action == "create"
        assert permission.is_active is True
        assert permission.role.name == "program_coordinator"
    
    def test_cascade_delete_permissions(self, db_session: Session):
        """Test that permissions are deleted when role is deleted"""
        # Create role
        role = AdminRole(
            name="test_role",
            display_name="Test Role",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        role_id = role.id
        
        # Create permissions
        perm1 = AdminPermission(role_id=role_id, resource="university", action="read", is_active=True)
        perm2 = AdminPermission(role_id=role_id, resource="university", action="update", is_active=True)
        db_session.add_all([perm1, perm2])
        db_session.commit()
        
        # Count permissions
        perm_count = db_session.query(AdminPermission).filter_by(role_id=role_id).count()
        assert perm_count == 2
        
        # Delete role
        db_session.delete(role)
        db_session.commit()
        
        # Verify permissions are deleted
        perm_count = db_session.query(AdminPermission).filter_by(role_id=role_id).count()
        assert perm_count == 0


class TestUserRole:
    """Test UserRole model"""
    
    def test_create_user_role_super_admin(self, db_session: Session):
        """Test creating user role assignment for super admin"""
        # Create user
        user = User(
            email="superadmin@example.com",
            password_hash="hashed_password",
            name="Super Admin"
        )
        db_session.add(user)
        
        # Create role
        role = AdminRole(
            name="super_admin",
            display_name="Super Administrator",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign role to user (no scope for super admin)
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Verify
        assert user_role.id is not None
        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.university_id is None
        assert user_role.program_id is None
        assert user_role.assigned_at is not None
        assert user_role.user.email == "superadmin@example.com"
        assert user_role.role.name == "super_admin"
    
    def test_create_user_role_university_admin(self, db_session: Session):
        """Test creating user role assignment with university scope"""
        # Create user
        user = User(
            email="univadmin@example.com",
            password_hash="hashed_password",
            name="University Admin"
        )
        db_session.add(user)
        
        # Create role
        role = AdminRole(
            name="university_admin",
            display_name="University Administrator",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        
        # Assign role with university scope
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=5,  # Scoped to university ID 5
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Verify
        assert user_role.university_id == 5
        assert user_role.program_id is None
    
    def test_create_user_role_program_coordinator(self, db_session: Session):
        """Test creating user role assignment with program scope"""
        # Create user
        user = User(
            email="coordinator@example.com",
            password_hash="hashed_password",
            name="Program Coordinator"
        )
        db_session.add(user)
        
        # Create role
        role = AdminRole(
            name="program_coordinator",
            display_name="Program Coordinator",
            is_active=True
        )
        db_session.add(role)
        
        # Create assigner user
        assigner = User(
            email="superadmin@example.com",
            password_hash="hashed_password",
            name="Super Admin"
        )
        db_session.add(assigner)
        db_session.commit()
        
        # Assign role with university and program scope
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=3,
            program_id=10,
            assigned_by=assigner.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Verify
        assert user_role.university_id == 3
        assert user_role.program_id == 10
        assert user_role.assigned_by == assigner.id
        assert user_role.assigner.email == "superadmin@example.com"
    
    def test_cascade_delete_user_roles(self, db_session: Session):
        """Test that user roles are deleted when user is deleted"""
        # Create user and role
        user = User(
            email="testuser@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        role = AdminRole(
            name="test_role",
            display_name="Test Role",
            is_active=True
        )
        db_session.add_all([user, role])
        db_session.commit()
        
        # Assign role
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id
        )
        db_session.add(user_role)
        db_session.commit()
        user_id = user.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify user_role is deleted
        role_count = db_session.query(UserRole).filter_by(user_id=user_id).count()
        assert role_count == 0


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_admin_role_permissions_relationship(self, db_session: Session):
        """Test the relationship between AdminRole and AdminPermission"""
        # Create role
        role = AdminRole(
            name="editor",
            display_name="Editor",
            is_active=True
        )
        db_session.add(role)
        db_session.commit()
        
        # Add multiple permissions
        perms = [
            AdminPermission(role_id=role.id, resource="course", action="create", is_active=True),
            AdminPermission(role_id=role.id, resource="course", action="update", is_active=True),
            AdminPermission(role_id=role.id, resource="course", action="delete", is_active=True),
        ]
        db_session.add_all(perms)
        db_session.commit()
        
        # Verify relationship
        assert len(role.permissions) == 3
        assert all(p.role.name == "editor" for p in perms)
    
    def test_user_roles_relationship(self, db_session: Session):
        """Test the relationship between User and UserRole"""
        # Create user
        user = User(
            email="multiuser@example.com",
            password_hash="hashed_password",
            name="Multi Role User"
        )
        db_session.add(user)
        
        # Create multiple roles
        role1 = AdminRole(name="role1", display_name="Role 1", is_active=True)
        role2 = AdminRole(name="role2", display_name="Role 2", is_active=True)
        db_session.add_all([role1, role2])
        db_session.commit()
        
        # Assign multiple roles to user
        user_role1 = UserRole(user_id=user.id, role_id=role1.id, university_id=1)
        user_role2 = UserRole(user_id=user.id, role_id=role2.id, university_id=2)
        db_session.add_all([user_role1, user_role2])
        db_session.commit()
        
        # Verify
        assert len(user.user_roles) == 2
        assert user.user_roles[0].role.name in ["role1", "role2"]
        assert user.user_roles[1].role.name in ["role1", "role2"]
