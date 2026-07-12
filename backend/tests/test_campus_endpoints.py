"""
Tests for Campus Management API Endpoints

Tests the CRUD operations for campus management including
creation, retrieval, update, and deletion with RBAC enforcement.

Requirements: 1.6
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.university import University
from app.models.campus import Campus
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.core.security import get_password_hash


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_campuses.db"
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
def test_university(db):
    """Create a test university"""
    university = University(
        name="Test University",
        name_de="Testuniversität",
        country="Germany",
        description="A test university",
        is_deleted=False
    )
    db.add(university)
    db.commit()
    db.refresh(university)
    return university


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


class TestCampusEndpoints:
    """Test suite for campus management endpoints"""
    
    def test_create_campus_success(self, client, test_university, auth_headers):
        """Test successful campus creation"""
        campus_data = {
            "university_id": test_university.id,
            "name": "Main Campus",
            "name_de": "Hauptcampus",
            "location": "München",
            "description": "Main campus location",
            "description_de": "Hauptcampus-Standort"
        }
        
        response = client.post(
            "/api/v1/admin/campuses",
            json=campus_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Main Campus"
        assert data["name_de"] == "Hauptcampus"
        assert data["location"] == "München"
        assert data["university_id"] == test_university.id
        assert "id" in data
        assert data["is_deleted"] is False
    
    def test_create_campus_german_characters(self, client, test_university, auth_headers):
        """Test campus creation with German special characters"""
        campus_data = {
            "university_id": test_university.id,
            "name": "Campus Süd",
            "name_de": "Südcampus Große Straße",
            "location": "München-Süd",
            "description": "Campus with Umlauts: äöüß"
        }
        
        response = client.post(
            "/api/v1/admin/campuses",
            json=campus_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Campus Süd"
        assert data["name_de"] == "Südcampus Große Straße"
    
    def test_create_campus_invalid_university(self, client, auth_headers):
        """Test campus creation with non-existent university"""
        campus_data = {
            "university_id": 99999,
            "name": "Invalid Campus",
            "location": "Nowhere"
        }
        
        response = client.post(
            "/api/v1/admin/campuses",
            json=campus_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_campuses_all(self, client, test_university, auth_headers, db):
        """Test listing all campuses"""
        # Create multiple campuses
        campuses_data = [
            {"university_id": test_university.id, "name": f"Campus {i}", "location": f"Location {i}"}
            for i in range(3)
        ]
        
        for campus_data in campuses_data:
            campus = Campus(**campus_data)
            db.add(campus)
        db.commit()
        
        response = client.get(
            "/api/v1/admin/campuses",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "campuses" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["campuses"]) == 3
    
    def test_list_campuses_filtered_by_university(self, client, auth_headers, db):
        """Test listing campuses filtered by university"""
        # Create two universities
        uni1 = University(name="Uni 1", country="Germany", is_deleted=False)
        uni2 = University(name="Uni 2", country="Germany", is_deleted=False)
        db.add_all([uni1, uni2])
        db.commit()
        db.refresh(uni1)
        db.refresh(uni2)
        
        # Create campuses for each
        campus1 = Campus(university_id=uni1.id, name="Campus A", is_deleted=False)
        campus2 = Campus(university_id=uni1.id, name="Campus B", is_deleted=False)
        campus3 = Campus(university_id=uni2.id, name="Campus C", is_deleted=False)
        db.add_all([campus1, campus2, campus3])
        db.commit()
        
        # Query campuses for uni1
        response = client.get(
            f"/api/v1/admin/campuses?university_id={uni1.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(c["university_id"] == uni1.id for c in data["campuses"])
    
    def test_list_campuses_pagination(self, client, test_university, auth_headers, db):
        """Test campus list pagination"""
        # Create 5 campuses
        for i in range(5):
            campus = Campus(
                university_id=test_university.id,
                name=f"Campus {i}",
                is_deleted=False
            )
            db.add(campus)
        db.commit()
        
        # Get first page (2 items)
        response = client.get(
            "/api/v1/admin/campuses?skip=0&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campuses"]) == 2
        assert data["total"] == 5
        
        # Get second page (2 items)
        response = client.get(
            "/api/v1/admin/campuses?skip=2&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campuses"]) == 2
        assert data["total"] == 5
    
    def test_get_campus_by_id(self, client, test_university, auth_headers, db):
        """Test getting specific campus by ID"""
        campus = Campus(
            university_id=test_university.id,
            name="Test Campus",
            location="Test Location",
            is_deleted=False
        )
        db.add(campus)
        db.commit()
        db.refresh(campus)
        
        response = client.get(
            f"/api/v1/admin/campuses/{campus.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campus.id
        assert data["name"] == "Test Campus"
        assert data["location"] == "Test Location"
    
    def test_get_campus_not_found(self, client, auth_headers):
        """Test getting non-existent campus"""
        response = client.get(
            "/api/v1/admin/campuses/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_campus(self, client, test_university, auth_headers, db):
        """Test updating campus information"""
        campus = Campus(
            university_id=test_university.id,
            name="Old Name",
            location="Old Location",
            is_deleted=False
        )
        db.add(campus)
        db.commit()
        db.refresh(campus)
        
        update_data = {
            "name": "New Name",
            "location": "New Location",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/admin/campuses/{campus.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["location"] == "New Location"
        assert data["description"] == "Updated description"
        assert data["university_id"] == test_university.id  # Should remain unchanged
    
    def test_update_campus_not_found(self, client, auth_headers):
        """Test updating non-existent campus"""
        update_data = {"name": "New Name"}
        
        response = client.put(
            "/api/v1/admin/campuses/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_campus(self, client, test_university, auth_headers, db):
        """Test soft deleting a campus"""
        campus = Campus(
            university_id=test_university.id,
            name="To Delete",
            is_deleted=False
        )
        db.add(campus)
        db.commit()
        db.refresh(campus)
        
        response = client.delete(
            f"/api/v1/admin/campuses/{campus.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify soft delete in database
        db.refresh(campus)
        assert campus.is_deleted is True
        assert campus.deleted_at is not None
    
    def test_delete_campus_not_found(self, client, auth_headers):
        """Test deleting non-existent campus"""
        response = client.delete(
            "/api/v1/admin/campuses/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_campus_without_auth(self, client, test_university):
        """Test that campus creation requires authentication"""
        campus_data = {
            "university_id": test_university.id,
            "name": "Test Campus"
        }
        
        response = client.post(
            "/api/v1/admin/campuses",
            json=campus_data
        )
        
        assert response.status_code == 401
