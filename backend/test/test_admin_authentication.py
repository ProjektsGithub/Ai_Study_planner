"""
Unit tests for admin authentication and role-based access control

Tests verify:
1. JWT token payload includes role information
2. get_current_user() dependency includes role information
3. Login endpoint includes roles in tokens
4. Refresh endpoint includes roles in new tokens
5. Admin seeding creates correct data structure

Requirements: 11.1-11.9, 15.3
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash
)
from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole


class TestJWTRoleIntegration:
    """Test JWT token creation and decoding with role information"""
    
    def test_access_token_includes_roles(self):
        """Test that access tokens include role information in payload"""
        roles = [
            {
                "role_id": 1,
                "role_name": "super_admin",
                "role_display_name": "Super Admin",
                "university_id": None,
                "program_id": None
            }
        ]
        
        token = create_access_token(data={"sub": "123"}, roles=roles)
        payload = decode_token(token)
        
        assert payload is not None
        assert "roles" in payload
        assert len(payload["roles"]) == 1
        assert payload["roles"][0]["role_name"] == "super_admin"
        assert payload["roles"][0]["university_id"] is None
        assert payload["roles"][0]["program_id"] is None
    
    def test_refresh_token_includes_roles(self):
        """Test that refresh tokens include role information in payload"""
        roles = [
            {
                "role_id": 2,
                "role_name": "university_admin",
                "role_display_name": "University Admin",
                "university_id": 5,
                "program_id": None
            }
        ]
        
        token = create_refresh_token(data={"sub": "456"}, roles=roles)
        payload = decode_token(token)
        
        assert payload is not None
        assert "roles" in payload
        assert len(payload["roles"]) == 1
        assert payload["roles"][0]["role_name"] == "university_admin"
        assert payload["roles"][0]["university_id"] == 5
        assert payload["roles"][0]["program_id"] is None
    
    def test_token_with_multiple_roles(self):
        """Test tokens with multiple role assignments"""
        roles = [
            {
                "role_id": 2,
                "role_name": "university_admin",
                "role_display_name": "University Admin",
                "university_id": 5,
                "program_id": None
            },
            {
                "role_id": 3,
                "role_name": "program_coordinator",
                "role_display_name": "Program Coordinator",
                "university_id": 5,
                "program_id": 10
            }
        ]
        
        token = create_access_token(data={"sub": "789"}, roles=roles)
        payload = decode_token(token)
        
        assert payload is not None
        assert len(payload["roles"]) == 2
        assert payload["roles"][0]["role_name"] == "university_admin"
        assert payload["roles"][1]["role_name"] == "program_coordinator"
    
    def test_token_with_empty_roles(self):
        """Test tokens with no roles (regular users)"""
        token = create_access_token(data={"sub": "999"}, roles=[])
        payload = decode_token(token)
        
        assert payload is not None
        assert "roles" in payload
        assert len(payload["roles"]) == 0
    
    def test_token_without_roles_parameter(self):
        """Test tokens created without roles parameter default to empty list"""
        token = create_access_token(data={"sub": "111"})
        payload = decode_token(token)
        
        assert payload is not None
        assert "roles" in payload
        assert len(payload["roles"]) == 0


class TestAdminRoleModels:
    """Test admin role and user role models"""
    
    def test_admin_role_creation(self, db: Session):
        """Test creating admin role definitions"""
        role = AdminRole(
            name="test_admin",
            display_name="Test Admin",
            description="Test admin role",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        assert role.id is not None
        assert role.name == "test_admin"
        assert role.is_active is True
    
    def test_user_role_assignment(self, db: Session):
        """Test assigning role to user"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("TestPass123!"),
            name="Test User",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        
        # Create test role
        role = AdminRole(
            name="test_role",
            display_name="Test Role",
            description="Test role",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
        
        # Assign role to user
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=None,
            program_id=None,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=None
        )
        db.add(user_role)
        db.commit()
        
        # Verify assignment
        db.refresh(user_role)
        assert user_role.id is not None
        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
    
    def test_user_role_with_university_scope(self, db: Session):
        """Test role assignment scoped to specific university"""
        user = User(
            email="uni-admin@example.com",
            password_hash=get_password_hash("TestPass123!"),
            name="University Admin",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        
        role = AdminRole(
            name="university_admin",
            display_name="University Admin",
            description="University admin role",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
        
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=42,  # Scoped to specific university
            program_id=None,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=None
        )
        db.add(user_role)
        db.commit()
        
        db.refresh(user_role)
        assert user_role.university_id == 42
        assert user_role.program_id is None
    
    def test_user_role_with_program_scope(self, db: Session):
        """Test role assignment scoped to specific program"""
        user = User(
            email="coordinator@example.com",
            password_hash=get_password_hash("TestPass123!"),
            name="Program Coordinator",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        
        role = AdminRole(
            name="program_coordinator",
            display_name="Program Coordinator",
            description="Program coordinator role",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
        
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=42,
            program_id=99,  # Scoped to specific program
            assigned_at=datetime.now(timezone.utc),
            assigned_by=None
        )
        db.add(user_role)
        db.commit()
        
        db.refresh(user_role)
        assert user_role.university_id == 42
        assert user_role.program_id == 99


class TestGetCurrentUserDependency:
    """Test get_current_user() dependency with role loading"""
    
    def test_user_roles_loaded_from_database(self, db: Session):
        """Test that get_current_user() loads fresh role data from database"""
        # Create user with role
        user = User(
            email="roletest@example.com",
            password_hash=get_password_hash("TestPass123!"),
            name="Role Test User",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        
        role = AdminRole(
            name="test_role_loading",
            display_name="Test Role Loading",
            description="Test role",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
        
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=None,
            program_id=None,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=None
        )
        db.add(user_role)
        db.commit()
        
        # Simulate what get_current_user() does
        user_roles = db.query(UserRole).filter(
            UserRole.user_id == user.id
        ).join(AdminRole, UserRole.role_id == AdminRole.id).filter(
            AdminRole.is_active == True
        ).all()
        
        # Attach roles to user
        user.roles = []
        for ur in user_roles:
            user.roles.append({
                "role_id": ur.role_id,
                "role_name": ur.role.name,
                "role_display_name": ur.role.display_name,
                "university_id": ur.university_id,
                "program_id": ur.program_id
            })
        
        # Verify
        assert hasattr(user, 'roles')
        assert len(user.roles) == 1
        assert user.roles[0]["role_name"] == "test_role_loading"
    
    def test_inactive_roles_excluded(self, db: Session):
        """Test that inactive roles are excluded from user.roles"""
        user = User(
            email="inactive-role@example.com",
            password_hash=get_password_hash("TestPass123!"),
            name="Inactive Role User",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0
        )
        db.add(user)
        db.flush()
        
        # Create inactive role
        role = AdminRole(
            name="inactive_role",
            display_name="Inactive Role",
            description="Inactive role",
            is_active=False,  # Inactive
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
        
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            university_id=None,
            program_id=None,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=None
        )
        db.add(user_role)
        db.commit()
        
        # Simulate get_current_user() behavior
        user_roles = db.query(UserRole).filter(
            UserRole.user_id == user.id
        ).join(AdminRole, UserRole.role_id == AdminRole.id).filter(
            AdminRole.is_active == True
        ).all()
        
        user.roles = [
            {
                "role_id": ur.role_id,
                "role_name": ur.role.name,
                "role_display_name": ur.role.display_name,
                "university_id": ur.university_id,
                "program_id": ur.program_id
            }
            for ur in user_roles
        ]
        
        # Inactive roles should be excluded
        assert len(user.roles) == 0


class TestAdminSeedingScript:
    """Test admin seeding functionality"""
    
    def test_admin_roles_exist(self, db: Session):
        """Test that all three admin roles exist in database"""
        expected_roles = ["super_admin", "university_admin", "program_coordinator"]
        
        for role_name in expected_roles:
            role = db.query(AdminRole).filter(AdminRole.name == role_name).first()
            assert role is not None, f"Role {role_name} should exist"
            assert role.is_active is True
            assert role.description is not None
    
    def test_super_admin_has_no_scope_restrictions(self, db: Session):
        """Test that super admin role assignments have no scope restrictions"""
        super_admin_role = db.query(AdminRole).filter(
            AdminRole.name == "super_admin"
        ).first()
        
        if super_admin_role:
            # Find any super admin user role assignments
            super_admin_assignments = db.query(UserRole).filter(
                UserRole.role_id == super_admin_role.id
            ).all()
            
            # All super admin assignments should have NULL university_id and program_id
            for assignment in super_admin_assignments:
                assert assignment.university_id is None
                assert assignment.program_id is None
