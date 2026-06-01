"""
Tests for profile management endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from app.main import app
from app.core.database import Base
from app.core.dependencies import get_db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.core.security import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_profile.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_user_and_login():
    """Helper function to create a test user and get auth token"""
    # Register user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "name": "Test User"
        }
    )
    assert response.status_code == 201
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return token


def test_create_profile():
    """Test profile creation"""
    token = create_test_user_and_login()
    
    response = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {"theme": "dark", "notifications": True}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["cursus"] == "Computer Science"
    assert data["academic_level"] == "Bachelor Year 3"
    assert data["weekly_study_goal"] == 25.0
    assert data["preferences"]["theme"] == "dark"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_profile():
    """Test profile retrieval"""
    token = create_test_user_and_login()
    
    # Create profile
    client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Get profile
    response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["cursus"] == "Computer Science"
    assert data["academic_level"] == "Bachelor Year 3"
    assert data["weekly_study_goal"] == 25.0


def test_get_profile_not_found():
    """Test getting profile when it doesn't exist"""
    token = create_test_user_and_login()
    
    response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_profile():
    """Test profile update"""
    token = create_test_user_and_login()
    
    # Create profile
    client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Update profile
    response = client.put(
        "/api/v1/profile",
        json={
            "weekly_study_goal": 30.0,
            "preferences": {"theme": "light"}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["weekly_study_goal"] == 30.0
    assert data["preferences"]["theme"] == "light"
    # Other fields should remain unchanged
    assert data["cursus"] == "Computer Science"
    assert data["academic_level"] == "Bachelor Year 3"


def test_update_profile_not_found():
    """Test updating profile when it doesn't exist"""
    token = create_test_user_and_login()
    
    response = client.put(
        "/api/v1/profile",
        json={"weekly_study_goal": 30.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_create_or_update_profile_updates_existing():
    """Test that POST endpoint updates existing profile"""
    token = create_test_user_and_login()
    
    # Create profile
    response1 = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    profile_id = response1.json()["id"]
    
    # Create again (should update)
    response2 = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Mathematics",
            "academic_level": "Master Year 1",
            "weekly_study_goal": 30.0,
            "preferences": {"theme": "dark"}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response2.status_code == 201
    data = response2.json()
    assert data["id"] == profile_id  # Same ID
    assert data["cursus"] == "Mathematics"
    assert data["weekly_study_goal"] == 30.0


def test_profile_validation_weekly_goal_too_low():
    """Test validation for weekly study goal below minimum"""
    token = create_test_user_and_login()
    
    response = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 0.5,  # Below minimum of 1.0
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


def test_profile_validation_weekly_goal_too_high():
    """Test validation for weekly study goal above maximum"""
    token = create_test_user_and_login()
    
    response = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 200.0,  # Above maximum of 168.0
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


def test_profile_validation_cursus_too_long():
    """Test validation for cursus exceeding max length"""
    token = create_test_user_and_login()
    
    response = client.post(
        "/api/v1/profile",
        json={
            "cursus": "A" * 101,  # Exceeds 100 character limit
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


def test_profile_requires_authentication():
    """Test that profile endpoints require authentication"""
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
    
    response = client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        }
    )
    assert response.status_code == 401


def test_delete_profile():
    """Test profile deletion"""
    token = create_test_user_and_login()
    
    # Create profile
    client.post(
        "/api/v1/profile",
        json={
            "cursus": "Computer Science",
            "academic_level": "Bachelor Year 3",
            "weekly_study_goal": 25.0,
            "preferences": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Delete profile
    response = client.delete(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()
    
    # Verify profile is deleted
    response = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
