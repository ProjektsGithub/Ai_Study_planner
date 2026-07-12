"""
Tests for Academic Track Management API Endpoints

Tests the CRUD operations for academic track management including
creation, retrieval, update, deletion, and dependent entity counting
with RBAC enforcement.

Requirements: 3.1-3.7
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.university import University
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.core.security import get_password_hash


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_academic_tracks.db"
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
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_university(db):
    """Create a test university"""
    university = University(
        name="Test University",
        name_de="Test Universität",
        country="Germany"
    )
    db.add(university)
    db.commit()
    db.refresh(university)
    return university


@pytest.fixture
def test_program(db, test_university):
    """Create a test study program"""
    program = StudyProgram(
        name="Computer Science",
        name_de="Informatik",
        code="CS"
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


class TestAcademicTrackCreation:
    """Test academic track creation"""
    
    def test_create_bachelor_track(self, client, auth_headers, test_program):
        """
        Test creating a bachelor academic track
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7
        """
        track_data = {
            "study_program_id": test_program.id,
            "name": "Bachelor in Computer Science",
            "name_de": "Bachelor Informatik",
            "level": "bachelor",
            "description": "3-year bachelor program",
            "description_de": "3-jähriges Bachelor-Programm",
            "total_ects_required": 180,
            "graduation_conditions": "Complete all required courses",
            "graduation_conditions_de": "Alle erforderlichen Kurse abschließen"
        }
        
        response = client.post(
            "/api/v1/admin/tracks",
            json=track_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == track_data["name"]
        assert data["name_de"] == track_data["name_de"]
        assert data["level"] == "bachelor"
        assert data["total_ects_required"] == 180
        assert "id" in data
        assert "created_at" in data
    
    def test_create_master_track(self, client, auth_headers, test_program):
        """
        Test creating a master academic track
        Requirements: 3.1, 3.2
        """
        track_data = {
            "study_program_id": test_program.id,
            "name": "Master in Computer Science",
            "name_de": "Master Informatik",
            "level": "master",
            "total_ects_required": 120
        }
        
        response = client.post(
            "/api/v1/admin/tracks",
            json=track_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["level"] == "master"
        assert data["total_ects_required"] == 120
    
    def test_create_doctorate_track(self, client, auth_headers, test_program):
        """
        Test creating a doctorate academic track
        Requirements: 3.1
        """
        track_data = {
            "study_program_id": test_program.id,
            "name": "Doctorate in Computer Science",
            "name_de": "Doktorat Informatik",
            "level": "doctorate",
            "total_ects_required": 180
        }
        
        response = client.post(
            "/api/v1/admin/tracks",
            json=track_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["level"] == "doctorate"
    
    def test_create_track_invalid_ects(self, client, auth_headers, test_program):
        """
        Test creating track with invalid ECTS (must be positive)
        Requirements: 3.6
        """
        track_data = {
            "study_program_id": test_program.id,
            "name": "Invalid Track",
            "level": "bachelor",
            "total_ects_required": -10  # Invalid: negative
        }
        
        response = client.post(
            "/api/v1/admin/tracks",
            json=track_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "positive integer" in response.json()["detail"].lower()
    
    def test_create_track_nonexistent_program(self, client, auth_headers):
        """
        Test creating track with non-existent study program
        Requirements: 3.7
        """
        track_data = {
            "study_program_id": 99999,  # Non-existent
            "name": "Invalid Track",
            "level": "bachelor",
            "total_ects_required": 180
        }
        
        response = client.post(
            "/api/v1/admin/tracks",
            json=track_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAcademicTrackRetrieval:
    """Test academic track retrieval"""
    
    def test_list_tracks(self, client, auth_headers, db, test_program):
        """
        Test listing all academic tracks
        Requirements: 3.1-3.7
        """
        # Create test tracks
        tracks = [
            AcademicTrack(
                study_program_id=test_program.id,
                name="Bachelor CS",
                level=TrackLevel.BACHELOR,
                total_ects_required=180
            ),
            AcademicTrack(
                study_program_id=test_program.id,
                name="Master CS",
                level=TrackLevel.MASTER,
                total_ects_required=120
            )
        ]
        for track in tracks:
            db.add(track)
        db.commit()
        
        response = client.get(
            "/api/v1/admin/tracks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert "total" in data
        assert data["total"] >= 2
    
    def test_list_tracks_filtered_by_program(self, client, auth_headers, db, test_program):
        """
        Test filtering tracks by study program
        Requirements: 3.4
        """
        # Create track
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        
        response = client.get(
            f"/api/v1/admin/tracks?study_program_id={test_program.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(t["study_program_id"] == test_program.id for t in data["tracks"])
    
    def test_list_tracks_filtered_by_level(self, client, auth_headers, db, test_program):
        """
        Test filtering tracks by level
        Requirements: 3.1
        """
        # Create tracks
        bachelor = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        master = AcademicTrack(
            study_program_id=test_program.id,
            name="Master CS",
            level=TrackLevel.MASTER,
            total_ects_required=120
        )
        db.add(bachelor)
        db.add(master)
        db.commit()
        
        response = client.get(
            "/api/v1/admin/tracks?level=bachelor",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(t["level"] == "bachelor" for t in data["tracks"])
    
    def test_get_track_by_id(self, client, auth_headers, db, test_program):
        """
        Test getting specific track by ID
        Requirements: 3.1-3.7
        """
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        response = client.get(
            f"/api/v1/admin/tracks/{track.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == track.id
        assert data["name"] == "Bachelor CS"


class TestAcademicTrackUpdate:
    """Test academic track updates"""
    
    def test_update_track_ects(self, client, auth_headers, db, test_program):
        """
        Test updating track ECTS requirement
        Requirements: 3.5, 3.6
        """
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        update_data = {
            "total_ects_required": 210
        }
        
        response = client.put(
            f"/api/v1/admin/tracks/{track.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_ects_required"] == 210
    
    def test_update_track_name(self, client, auth_headers, db, test_program):
        """
        Test updating track name
        Requirements: 3.5
        """
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        update_data = {
            "name": "Bachelor in Computer Science",
            "name_de": "Bachelor Informatik"
        }
        
        response = client.put(
            f"/api/v1/admin/tracks/{track.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Bachelor in Computer Science"
        assert data["name_de"] == "Bachelor Informatik"


class TestAcademicTrackDeletion:
    """Test academic track deletion"""
    
    def test_delete_track(self, client, auth_headers, db, test_program):
        """
        Test soft deleting an academic track
        Requirements: 3.1-3.7
        """
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        response = client.delete(
            f"/api/v1/admin/tracks/{track.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dependent_counts" in data
    
    def test_get_dependent_counts(self, client, auth_headers, db, test_program):
        """
        Test getting dependent entity counts
        Requirements: 3.1-3.7
        """
        track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        response = client.get(
            f"/api/v1/admin/tracks/{track.id}/dependents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "semesters_count" in data
        assert "courses_count" in data
