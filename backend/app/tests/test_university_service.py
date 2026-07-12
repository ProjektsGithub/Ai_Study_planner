"""
Unit tests for UniversityService

Tests CRUD operations, dependent entity counting, pagination, and filtering.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.university_service import UniversityService
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram, university_programs
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.semester import Semester
from app.models.course import Course
from app.models.teaching_unit import TeachingUnit


@pytest.mark.asyncio
class TestUniversityService:
    """Test suite for UniversityService"""
    
    async def test_create_university_success(self, db_session: Session):
        """Test successful university creation"""
        service = UniversityService(db_session)
        
        university_data = {
            "name": "Technical University of Munich",
            "name_de": "Technische Universität München",
            "country": "Germany",
            "description": "Leading technical university in Germany"
        }
        
        university = await service.create_university(university_data)
        
        assert university.id is not None
        assert university.name == "Technical University of Munich"
        assert university.name_de == "Technische Universität München"
        assert university.country == "Germany"
        assert university.is_deleted is False
    
    async def test_create_university_duplicate_name(self, db_session: Session):
        """Test that duplicate university names are rejected"""
        service = UniversityService(db_session)
        
        university_data = {
            "name": "University of Berlin",
            "country": "Germany"
        }
        
        # Create first university
        await service.create_university(university_data)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await service.create_university(university_data)
    
    async def test_get_universities_pagination(self, db_session: Session):
        """Test pagination of universities list"""
        service = UniversityService(db_session)
        
        # Create multiple universities
        for i in range(5):
            await service.create_university({
                "name": f"University {i}",
                "country": "Germany"
            })
        
        # Get first page
        universities, total = await service.get_universities(skip=0, limit=3)
        assert len(universities) == 3
        assert total == 5
        
        # Get second page
        universities, total = await service.get_universities(skip=3, limit=3)
        assert len(universities) == 2
        assert total == 5
    
    async def test_get_universities_search_filter(self, db_session: Session):
        """Test search filtering for universities"""
        service = UniversityService(db_session)
        
        await service.create_university({
            "name": "Munich University",
            "country": "Germany"
        })
        await service.create_university({
            "name": "Berlin University",
            "country": "Germany"
        })
        
        # Search for Munich
        universities, total = await service.get_universities(
            filters={"search": "Munich"}
        )
        assert len(universities) == 1
        assert universities[0].name == "Munich University"
    
    async def test_get_university_by_id(self, db_session: Session):
        """Test retrieving university by ID"""
        service = UniversityService(db_session)
        
        created = await service.create_university({
            "name": "Test University",
            "country": "Germany"
        })
        
        retrieved = await service.get_university_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test University"
    
    async def test_update_university_success(self, db_session: Session):
        """Test successful university update"""
        service = UniversityService(db_session)
        
        university = await service.create_university({
            "name": "Original Name",
            "country": "Germany"
        })
        
        updated = await service.update_university(university.id, {
            "name": "Updated Name",
            "description": "New description"
        })
        
        assert updated.name == "Updated Name"
        assert updated.description == "New description"
        assert updated.updated_at > university.created_at
    
    async def test_update_university_duplicate_name(self, db_session: Session):
        """Test that updating to duplicate name is rejected"""
        service = UniversityService(db_session)
        
        uni1 = await service.create_university({
            "name": "University One",
            "country": "Germany"
        })
        uni2 = await service.create_university({
            "name": "University Two",
            "country": "Germany"
        })
        
        # Try to update uni2 to have uni1's name
        with pytest.raises(ValueError, match="already exists"):
            await service.update_university(uni2.id, {"name": "University One"})
    
    async def test_delete_university_soft_delete(self, db_session: Session):
        """Test soft delete of university"""
        service = UniversityService(db_session)
        
        university = await service.create_university({
            "name": "To Delete",
            "country": "Germany"
        })
        
        result = await service.delete_university(university.id)
        
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        
        # Verify soft delete
        db_session.refresh(university)
        assert university.is_deleted is True
        assert university.deleted_at is not None
        
        # Should not appear in get_universities
        universities, total = await service.get_universities()
        assert university.id not in [u.id for u in universities]
    
    async def test_get_dependent_counts(self, db_session: Session):
        """Test counting dependent entities"""
        service = UniversityService(db_session)
        
        # Create university
        university = await service.create_university({
            "name": "Test University",
            "country": "Germany"
        })
        
        # Create campus
        campus = Campus(
            university_id=university.id,
            name="Main Campus",
            location="City Center"
        )
        db_session.add(campus)
        
        # Create study program and link it
        program = StudyProgram(
            name="Computer Science",
            code="CS"
        )
        db_session.add(program)
        db_session.commit()
        db_session.refresh(program)
        
        # Link program to university
        stmt = university_programs.insert().values(
            university_id=university.id,
            study_program_id=program.id,
            created_at=datetime.now(timezone.utc)
        )
        db_session.execute(stmt)
        
        # Create academic track
        track = AcademicTrack(
            study_program_id=program.id,
            name="Bachelor CS",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db_session.add(track)
        db_session.commit()
        db_session.refresh(track)
        
        # Create semester
        semester = Semester(
            academic_track_id=track.id,
            name="S1",
            semester_number=1
        )
        db_session.add(semester)
        db_session.commit()
        db_session.refresh(semester)
        
        # Create course
        course = Course(
            semester_id=semester.id,
            name="Introduction to Programming",
            ects_credits=6,
            coefficient=1.0,
            difficulty_level=2
        )
        db_session.add(course)
        db_session.commit()
        
        # Get dependent counts
        counts = await service.get_dependent_counts(university.id)
        
        assert counts["campuses"] == 1
        assert counts["programs"] == 1
        assert counts["tracks"] == 1
        assert counts["semesters"] == 1
        assert counts["courses"] == 1
    
    async def test_create_campus_success(self, db_session: Session):
        """Test successful campus creation"""
        service = UniversityService(db_session)
        
        university = await service.create_university({
            "name": "Test University",
            "country": "Germany"
        })
        
        campus = await service.create_campus({
            "university_id": university.id,
            "name": "Main Campus",
            "location": "Downtown"
        })
        
        assert campus.id is not None
        assert campus.university_id == university.id
        assert campus.name == "Main Campus"
        assert campus.is_deleted is False
    
    async def test_create_campus_invalid_university(self, db_session: Session):
        """Test that creating campus with invalid university fails"""
        service = UniversityService(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await service.create_campus({
                "university_id": 99999,
                "name": "Test Campus"
            })
    
    async def test_get_campuses_by_university(self, db_session: Session):
        """Test filtering campuses by university"""
        service = UniversityService(db_session)
        
        uni1 = await service.create_university({
            "name": "University One",
            "country": "Germany"
        })
        uni2 = await service.create_university({
            "name": "University Two",
            "country": "Germany"
        })
        
        await service.create_campus({
            "university_id": uni1.id,
            "name": "Uni1 Campus 1"
        })
        await service.create_campus({
            "university_id": uni1.id,
            "name": "Uni1 Campus 2"
        })
        await service.create_campus({
            "university_id": uni2.id,
            "name": "Uni2 Campus 1"
        })
        
        # Get campuses for uni1
        campuses, total = await service.get_campuses(university_id=uni1.id)
        assert len(campuses) == 2
        assert total == 2
        assert all(c.university_id == uni1.id for c in campuses)
    
    async def test_update_campus(self, db_session: Session):
        """Test updating campus information"""
        service = UniversityService(db_session)
        
        university = await service.create_university({
            "name": "Test University",
            "country": "Germany"
        })
        
        campus = await service.create_campus({
            "university_id": university.id,
            "name": "Original Name",
            "location": "Original Location"
        })
        
        updated = await service.update_campus(campus.id, {
            "name": "Updated Name",
            "location": "New Location"
        })
        
        assert updated.name == "Updated Name"
        assert updated.location == "New Location"
    
    async def test_delete_campus(self, db_session: Session):
        """Test soft delete of campus"""
        service = UniversityService(db_session)
        
        university = await service.create_university({
            "name": "Test University",
            "country": "Germany"
        })
        
        campus = await service.create_campus({
            "university_id": university.id,
            "name": "Campus to Delete"
        })
        
        result = await service.delete_campus(campus.id)
        
        assert result["success"] is True
        
        # Verify soft delete
        db_session.refresh(campus)
        assert campus.is_deleted is True
        assert campus.deleted_at is not None
