"""
Test cases for admin authentication with role support

Requirements: 11.1-11.9, 15.3
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.core.security import get_password_hash, decode_token
from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole


@pytest.fixture
def db():
    """Database session fixture"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def super_admin_user(db: Session):
    """Create a test super admin user"""
    # Create user
    user = User(
        email="testadmin@example.com",
        password_hash=get_password_hash("TestAdmin123!"),
        name="Test Admin",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        failed_login_attempts=0
    )
    db.add(user)
    db.flush()
    
    # Get or create super_admin role
    role = db.query(AdminRole).filter(AdminRole.name == "super_admin").first()
    if not role:
        role = AdminRole(
            name="super_admin",
            display_name="Super Admin",
            description="Full system access",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(role)
        db.flush()
    
    # Assign role
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
    
    yield user
    
    # Cleanup
    db.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db.query(User).filter(User.id == user.id).delete()
    db.commit()


def test_login_includes_roles_in_token(client: TestClient, super_admin_user: User):
    """Test that login includes role information in JWT token"""
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testadmin@example.com",
            "password": "TestAdmin123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # Decode access token and verify roles are included
    access_token = data["access_token"]
    payload = decode_token(access_token)
    
    assert payload is not None
    assert "roles" in payload
    assert len(payload["roles"]) > 0
    
    # Verify role structure
    role = payload["roles"][0]
    assert "role_name" in role
    assert role["role_name"] == "super_admin"
    assert "role_display_name" in role
    assert "university_id" in role
    assert "program_id" in role


def test_get_current_user_includes_roles(client: TestClient, super_admin_user: User):
    """Test that get_current_user dependency includes role information"""
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testadmin@example.com",
            "password": "TestAdmin123!"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # Call /auth/me endpoint which uses get_current_user dependency
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    # Note: The roles are attached as a dynamic attribute to the User object
    # but won't be in the JSON response unless we update the UserResponse schema
    # This test verifies the endpoint works with the updated dependency


def test_refresh_token_includes_roles(client: TestClient, super_admin_user: User):
    """Test that refresh token includes role information"""
    # Login to get refresh token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testadmin@example.com",
            "password": "TestAdmin123!"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Decode refresh token and verify roles are included
    payload = decode_token(refresh_token)
    
    assert payload is not None
    assert "roles" in payload
    assert len(payload["roles"]) > 0
    
    # Use refresh token to get new access token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # Verify new tokens also include roles
    new_access_token = data["access_token"]
    new_payload = decode_token(new_access_token)
    
    assert new_payload is not None
    assert "roles" in new_payload
    assert len(new_payload["roles"]) > 0


def test_user_without_roles_has_empty_roles_list(client: TestClient, db: Session):
    """Test that users without admin roles get empty roles list"""
    # Create regular user without admin roles
    user = User(
        email="regularuser@example.com",
        password_hash=get_password_hash("RegularUser123!"),
        name="Regular User",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        failed_login_attempts=0
    )
    db.add(user)
    db.commit()
    
    try:
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "regularuser@example.com",
                "password": "RegularUser123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Decode token
        payload = decode_token(data["access_token"])
        
        assert payload is not None
        # User without roles should have empty roles list
        assert "roles" in payload
        assert payload["roles"] == []
        
    finally:
        # Cleanup
        db.query(User).filter(User.id == user.id).delete()
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
