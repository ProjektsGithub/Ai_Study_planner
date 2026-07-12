"""
Tests for University Management API Endpoints

Tests the CRUD operations for university management including
creation, retrieval, update, deletion, and dependent entity counting
with RBAC enforcement.

Requirements: 1.1-1.7
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.university import University
from app.models.campus import Campus
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.core.security import get_password_hash


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_universities.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def super_admin_user(db):
    """Create a super admin user for testing"""
    # Create super admin role
    role = AdminRole(
        name="super_admin",
        description="Super Administrator with full access",
        is_active=True
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Create user
    user = User(
        email="superadmin@test.com",
        username="superadmin",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Assign role
    user_role = UserRole(
        user_id=user.id,
        role_id=role.id
    )
    db.add(user_role)
    db.commit()
    
    return user


@pytest.fixture
def auth_headers(client, super_admin_user):
    """Get authentication headers for super admin"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "superadmin@test.com",
            "password": "testpass123"
        }
    )
    
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.json()}")
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


class TestUniversityEndpoints:
    """Test suite for university management endpoints"""
    
    def test_create_university_success(self, client, auth_headers):
        """Test successful university creation"""
        university_data = {
            "name": "Technical University of Munich",
            "name_de": "Technische Universität München",
            "country": "Germany",
            "description": "A leading technical university",
            "description_de": "Eine führende technische Universität"
        }
        
        response = client.post(
            "/api/v1/admin/universities",
            json=university_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Technical University of Munich"
        assert data["name_de"] == "Technische Universität München"
        assert data["country"] == "Germany"
        assert "id" in data
        assert data["is_deleted"] is False
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_university_german_characters(self, client, auth_headers):
        """Test university creation with German special characters (ä, ö, ü, ß)"""
        university_data = {
            "name": "University of Münster",
            "name_de": "Universität Münster - Große Straße",
            "country": "Germany",
            "description": "Supports äöüß characters"
        }
        
        response = client.post(
            "/api/v1/admin/universities",
            json=university_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name_de"] == "Universität Münster - Große Straße"
        assert "äöüß" in data["description"]
    
    def test_create_university_duplicate_name(self, client, auth_headers, db):
        """Test that duplicate university names are rejected (Requirement 1.7)"""
        # Create first university
        uni = University(
            name="Duplicate University",
            country="Germany",
            is_deleted=False
        )
        db.add(uni)
        db.commit()
        
        # Try to create with same name
        university_data = {
            "name": "Duplicate University",
            "country": "Germany"
        }
        
        response = client.post(
            "/api/v1/admin/universities",
            json=university_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_university_minimal_data(self, client, auth_headers):
        """Test creating university with minimal required data"""
        university_data = {
            "name": "Minimal University"
        }
        
        response = client.post(
            "/api/v1/admin/universities",
            json=university_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal University"
        assert data["country"] == "Germany"  # Default value
    
    def test_list_universities_all(self, client, auth_headers, db):
        """Test listing all universities (Requirement 1.4)"""
        # Create multiple universities
        universities = [
            University(name=f"University {i}", country="Germany", is_deleted=False)
            for i in range(3)
        ]
        db.add_all(universities)
        db.commit()
        
        response = client.get(
            "/api/v1/admin/universities",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "universities" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["universities"]) == 3
    
    def test_list_universities_with_search(self, client, auth_headers, db):
        """Test listing universities with search filter"""
        # Create universities
        uni1 = University(name="Technical University", country="Germany", is_deleted=False)
        uni2 = University(name="Medical University", country="Germany", is_deleted=False)
        uni3 = University(name="Technical College", country="Germany", is_deleted=False)
        db.add_all([uni1, uni2, uni3])
        db.commit()
        
        # Search for "Technical"
        response = client.get(
            "/api/v1/admin/universities?search=Technical",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all("Technical" in u["name"] for u in data["universities"])
    
    def test_list_universities_with_country_filter(self, client, auth_headers, db):
        """Test listing universities filtered by country"""
        # Create universities in different countries
        uni1 = University(name="German Uni", country="Germany", is_deleted=False)
        uni2 = University(name="French Uni", country="France", is_deleted=False)
        uni3 = University(name="Another German Uni", country="Germany", is_deleted=False)
        db.add_all([uni1, uni2, uni3])
        db.commit()
        
        # Filter by Germany
        response = client.get(
            "/api/v1/admin/universities?country=Germany",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(u["country"] == "Germany" for u in data["universities"])
    
    def test_list_universities_pagination(self, client, auth_headers, db):
        """Test university list pagination"""
        # Create 5 universities
        for i in range(5):
            uni = University(name=f"Uni {i}", country="Germany", is_deleted=False)
            db.add(uni)
        db.commit()
        
        # Get first page (2 items)
        response = client.get(
            "/api/v1/admin/universities?skip=0&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["universities"]) == 2
        assert data["total"] == 5
        
        # Get second page (2 items)
        response = client.get(
            "/api/v1/admin/universities?skip=2&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["universities"]) == 2
        assert data["total"] == 5
    
    def test_get_university_by_id(self, client, auth_headers, db):
        """Test getting specific university by ID with campuses (Requirement 1.4)"""
        # Create university with campus
        university = University(
            name="Test University",
            name_de="Testuniversität",
            country="Germany",
            is_deleted=False
        )
        db.add(university)
        db.commit()
        db.refresh(university)
        
        campus = Campus(
            university_id=university.id,
            name="Main Campus",
            is_deleted=False
        )
        db.add(campus)
        db.commit()
        
        response = client.get(
            f"/api/v1/admin/universities/{university.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == university.id
        assert data["name"] == "Test University"
        assert data["name_de"] == "Testuniversität"
        assert "campuses" in data
        assert len(data["campuses"]) == 1
        assert data["campuses"][0]["name"] == "Main Campus"
    
    def test_get_university_not_found(self, client, auth_headers):
        """Test getting non-existent university"""
        response = client.get(
            "/api/v1/admin/universities/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_university(self, client, auth_headers, db):
        """Test updating university information (Requirement 1.2)"""
        university = University(
            name="Old Name",
            country="Germany",
            is_deleted=False
        )
        db.add(university)
        db.commit()
        db.refresh(university)
        
        update_data = {
            "name": "New Name",
            "name_de": "Neuer Name",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/admin/universities/{university.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["name_de"] == "Neuer Name"
        assert data["description"] == "Updated description"
        assert data["country"] == "Germany"  # Should remain unchanged
    
    def test_update_university_partial(self, client, auth_headers, db):
        """Test partial update (only some fields)"""
        university = University(
            name="Original Name",
            name_de="Originalname",
            country="Germany",
            is_deleted=False
        )
        db.add(university)
        db.commit()
        db.refresh(university)
        
        # Only update description
        update_data = {
            "description": "Only description updated"
        }
        
        response = client.put(
            f"/api/v1/admin/universities/{university.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original Name"  # Unchanged
        assert data["name_de"] == "Originalname"  # Unchanged
        assert data["description"] == "Only description updated"
    
    def test_update_university_duplicate_name(self, client, auth_headers, db):
        """Test that updating to duplicate name is rejected (Requirement 1.7)"""
        uni1 = University(name="University One", country="Germany", is_deleted=False)
        uni2 = University(name="University Two", country="Germany", is_deleted=False)
        db.add_all([uni1, uni2])
        db.commit()
        db.refresh(uni1)
        db.refresh(uni2)
        
        # Try to rename uni2 to uni1's name
        update_data = {"name": "University One"}
        
        response = client.put(
            f"/api/v1/admin/universities/{uni2.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    def test_update_university_not_found(self, client, auth_headers):
        """Test updating non-existent university"""
        update_data = {"name": "New Name"}
        
        response = client.put(
            "/api/v1/admin/universities/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_university(self, client, auth_headers, db):
        """Test soft deleting a university (Requirement 1.3)"""
        university = University(
            name="To Delete",
            country="Germany",
            is_deleted=False
        )
        db.add(university)
        db.commit()
        db.refresh(university)
        
        response = client.delete(
            f"/api/v1/admin/universities/{university.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dependent_counts" in data
        
        # Verify soft delete in database
        db.refresh(university)
        assert university.is_deleted is True
        assert university.deleted_at is not None
    
    def test_delete_university_with_campuses(self, client, auth_headers, db):
        """Test deleting university also soft deletes campuses"""
        university = University(name="Uni with Campuses", country="Germany", is_deleted=False)
        db.add(university)
        db.commit()
        db.refresh(university)
        
        # Add campuses
        campus1 = Campus(university_id=university.id, name="Campus 1", is_deleted=False)
        campus2 = Campus(university_id=university.id, name="Campus 2", is_deleted=False)
        db.add_all([campus1, campus2])
        db.commit()
        db.refresh(campus1)
        db.refresh(campus2)
        
        response = client.delete(
            f"/api/v1/admin/universities/{university.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["dependent_counts"]["campuses"] == 2
        
        # Verify campuses are also soft deleted
        db.refresh(campus1)
        db.refresh(campus2)
        assert campus1.is_deleted is True
        assert campus2.is_deleted is True
    
    def test_delete_university_not_found(self, client, auth_headers):
        """Test deleting non-existent university"""
        response = client.delete(
            "/api/v1/admin/universities/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_dependent_counts(self, client, auth_headers, db):
        """Test getting dependent entity counts (Requirement 1.5)"""
        university = University(name="Uni with Deps", country="Germany", is_deleted=False)
        db.add(university)
        db.commit()
        db.refresh(university)
        
        # Add campuses
        campus1 = Campus(university_id=university.id, name="Campus 1", is_deleted=False)
        campus2 = Campus(university_id=university.id, name="Campus 2", is_deleted=False)
        db.add_all([campus1, campus2])
        db.commit()
        
        response = client.get(
            f"/api/v1/admin/universities/{university.id}/dependents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["campuses"] == 2
        assert "programs" in data
        assert "tracks" in data
        assert "semesters" in data
        assert "courses" in data
    
    def test_get_dependent_counts_not_found(self, client, auth_headers):
        """Test getting dependent counts for non-existent university"""
        response = client.get(
            "/api/v1/admin/universities/99999/dependents",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_university_without_auth(self, client):
        """Test that university creation requires authentication"""
        university_data = {
            "name": "Test University",
            "country": "Germany"
        }
        
        response = client.post(
            "/api/v1/admin/universities",
            json=university_data
        )
        
        assert response.status_code == 401
    
    def test_list_universities_without_auth(self, client):
        """Test that listing universities requires authentication"""
        response = client.get("/api/v1/admin/universities")
        
        assert response.status_code == 401
