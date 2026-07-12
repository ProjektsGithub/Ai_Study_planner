"""
Test cases for university management API endpoints

Requirements: 1.1-1.7, 11.1-11.9
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.models.university import University


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


@pytest.fixture
def auth_headers(client: TestClient, super_admin_user: User):
    """Get authentication headers with access token"""
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
    access_token = data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


def test_create_university_success(client: TestClient, auth_headers: dict, db: Session):
    """Test successful university creation"""
    # Create university
    response = client.post(
        "/api/v1/admin/universities",
        json={
            "name": "Technical University Munich",
            "name_de": "Technische Universität München",
            "country": "Germany",
            "description": "Leading technical university",
            "description_de": "Führende technische Universität"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["name"] == "Technical University Munich"
    assert data["name_de"] == "Technische Universität München"
    assert data["country"] == "Germany"
    assert data["is_deleted"] is False
    
    # Cleanup
    university_id = data["id"]
    db.query(University).filter(University.id == university_id).delete()
    db.commit()


def test_create_university_duplicate_name(client: TestClient, auth_headers: dict, db: Session):
    """Test that duplicate university names are rejected"""
    # Create first university
    university1 = University(
        name="Test University",
        country="Germany",
        is_deleted=False
    )
    db.add(university1)
    db.commit()
    
    # Try to create second university with same name
    response = client.post(
        "/api/v1/admin/universities",
        json={
            "name": "Test University",
            "country": "Germany"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()
    
    # Cleanup
    db.query(University).filter(University.id == university1.id).delete()
    db.commit()


def test_list_universities(client: TestClient, auth_headers: dict, db: Session):
    """Test listing universities with pagination"""
    # Create test universities
    uni1 = University(name="University 1", country="Germany", is_deleted=False)
    uni2 = University(name="University 2", country="Germany", is_deleted=False)
    db.add_all([uni1, uni2])
    db.commit()
    
    # List universities
    response = client.get(
        "/api/v1/admin/universities?skip=0&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "universities" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["universities"]) >= 2
    
    # Cleanup
    db.query(University).filter(University.id.in_([uni1.id, uni2.id])).delete()
    db.commit()


def test_get_university_details(client: TestClient, auth_headers: dict, db: Session):
    """Test getting university details"""
    # Create test university
    university = University(
        name="Test University",
        name_de="Test Universität",
        country="Germany",
        description="Test description",
        is_deleted=False
    )
    db.add(university)
    db.commit()
    
    # Get university details
    response = client.get(
        f"/api/v1/admin/universities/{university.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == university.id
    assert data["name"] == "Test University"
    assert data["name_de"] == "Test Universität"
    assert "campuses" in data  # Should include campuses
    
    # Cleanup
    db.query(University).filter(University.id == university.id).delete()
    db.commit()


def test_update_university(client: TestClient, auth_headers: dict, db: Session):
    """Test updating university information"""
    # Create test university
    university = University(
        name="Original Name",
        country="Germany",
        is_deleted=False
    )
    db.add(university)
    db.commit()
    
    # Update university
    response = client.put(
        f"/api/v1/admin/universities/{university.id}",
        json={
            "name": "Updated Name",
            "description": "New description"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"
    assert data["country"] == "Germany"  # Unchanged field
    
    # Cleanup
    db.query(University).filter(University.id == university.id).delete()
    db.commit()


def test_delete_university(client: TestClient, auth_headers: dict, db: Session):
    """Test deleting university (soft delete)"""
    # Create test university
    university = University(
        name="University to Delete",
        country="Germany",
        is_deleted=False
    )
    db.add(university)
    db.commit()
    university_id = university.id
    
    # Delete university
    response = client.delete(
        f"/api/v1/admin/universities/{university_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "dependent_counts" in data
    
    # Verify soft delete
    db.refresh(university)
    assert university.is_deleted is True
    assert university.deleted_at is not None
    
    # Cleanup
    db.query(University).filter(University.id == university_id).delete()
    db.commit()


def test_get_dependent_counts(client: TestClient, auth_headers: dict, db: Session):
    """Test getting dependent entity counts"""
    # Create test university
    university = University(
        name="Test University",
        country="Germany",
        is_deleted=False
    )
    db.add(university)
    db.commit()
    
    # Get dependent counts
    response = client.get(
        f"/api/v1/admin/universities/{university.id}/dependents",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "campuses" in data
    assert "programs" in data
    assert "tracks" in data
    assert "semesters" in data
    assert "courses" in data
    assert isinstance(data["campuses"], int)
    
    # Cleanup
    db.query(University).filter(University.id == university.id).delete()
    db.commit()


def test_create_university_without_auth(client: TestClient):
    """Test that creating university without authentication fails"""
    response = client.post(
        "/api/v1/admin/universities",
        json={
            "name": "Test University",
            "country": "Germany"
        }
    )
    
    assert response.status_code == 401


def test_list_universities_with_search(client: TestClient, auth_headers: dict, db: Session):
    """Test listing universities with search filter"""
    # Create test universities
    uni1 = University(name="Munich Technical University", country="Germany", is_deleted=False)
    uni2 = University(name="Berlin University", country="Germany", is_deleted=False)
    db.add_all([uni1, uni2])
    db.commit()
    
    # Search for "Munich"
    response = client.get(
        "/api/v1/admin/universities?search=Munich",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should find at least the Munich university
    munich_found = any("Munich" in uni["name"] for uni in data["universities"])
    assert munich_found
    
    # Cleanup
    db.query(University).filter(University.id.in_([uni1.id, uni2.id])).delete()
    db.commit()
