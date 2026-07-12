"""
Unit tests for ValidationService - Super Admin Platform business rules

Tests cover:
- Circular dependency detection for prerequisite chains
- ECTS hierarchy validation (graduation >= year >= semester)
- Semester structure validation for Bachelor (S1-S6) and Master (S1-S4)
- Import data validation with detailed error messages
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.services.validation_service import ValidationService
from app.models.course import Course
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.semester import Semester
from app.models.validation_rule import ValidationRule, RuleType
from app.models.study_program import StudyProgram
from app.models.university import University
from app.core.database import Base


@pytest.fixture
def db_session():
    """Create an in-memory test database session"""
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def validation_service(db_session):
    """Create ValidationService instance"""
    return ValidationService(db_session)


@pytest.fixture
def sample_university(db_session):
    """Create a sample university"""
    university = University(
        name="Test University",
        name_de="Test Universität",
        country="Germany"
    )
    db_session.add(university)
    db_session.commit()
    db_session.refresh(university)
    return university


@pytest.fixture
def sample_program(db_session, sample_university):
    """Create a sample study program"""
    program = StudyProgram(
        name="Computer Science",
        name_de="Informatik",
        description="CS Program"
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


@pytest.fixture
def sample_bachelor_track(db_session, sample_program):
    """Create a sample Bachelor track"""
    track = AcademicTrack(
        study_program_id=sample_program.id,
        name="Bachelor Computer Science",
        level=TrackLevel.BACHELOR,
        total_ects_required=180
    )
    db_session.add(track)
    db_session.commit()
    db_session.refresh(track)
    return track


@pytest.fixture
def sample_master_track(db_session, sample_program):
    """Create a sample Master track"""
    track = AcademicTrack(
        study_program_id=sample_program.id,
        name="Master Computer Science",
        level=TrackLevel.MASTER,
        total_ects_required=120
    )
    db_session.add(track)
    db_session.commit()
    db_session.refresh(track)
    return track


class TestPrerequisiteChainValidation:
    """Test circular dependency detection for prerequisite chains"""
    
    @pytest.mark.asyncio
    async def test_valid_prerequisite_no_cycle(self, db_session, validation_service, sample_bachelor_track):
        """Test valid prerequisite relationship with no cycles"""
        # Create semesters
        s1 = Semester(academic_track_id=sample_bachelor_track.id, name="S1", semester_number=1)
        s2 = Semester(academic_track_id=sample_bachelor_track.id, name="S2", semester_number=2)
        db_session.add_all([s1, s2])
        db_session.commit()
        
        # Create courses
        course1 = Course(
            semester_id=s1.id,
            name="Intro to Programming",
            ects_credits=6,
            coefficient=1.0,
            difficulty_level=1
        )
        course2 = Course(
            semester_id=s2.id,
            name="Data Structures",
            ects_credits=6,
            coefficient=1.0,
            difficulty_level=2
        )
        db_session.add_all([course1, course2])
        db_session.commit()
        
        # Validate: course2 can have course1 as prerequisite
        is_valid, error_msg = await validation_service.validate_prerequisite_chain(
            db_session, course2.id, course1.id
        )
        
        assert is_valid is True
        assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_circular_dependency_direct(self, db_session, validation_service, sample_bachelor_track):
        """Test detection of direct circular dependency (A -> B -> A)"""
        # Create semester
        s1 = Semester(academic_track_id=sample_bachelor_track.id, name="S1", semester_number=1)
        db_session.add(s1)
        db_session.commit()
        
        # Create courses
        course1 = Course(
            semester_id=s1.id,
            name="Course A",
            ects_credits=6,
            coefficient=1.0,
            difficulty_level=1
        )
        course2 = Course(
            semester_id=s1.id,
            name="Course B",
            ects_credits=6,
            coefficient=1.0,
            difficulty_level=1
        )
        db_session.add_all([course1, course2])
        db_session.commit()
        
        # Create prerequisite: course2 requires course1
        course2.prerequisites.append(course1)
        db_session.commit()
        
        # Try to add: course1 requires course2 (creates cycle)
        is_valid, error_msg = await validation_service.validate_prerequisite_chain(
            db_session, course1.id, course2.id
        )
        
        assert is_valid is False
        assert error_msg is not None
        assert "Circular dependency detected" in error_msg
        assert "Course A" in error_msg
        assert "Course B" in error_msg
    
    @pytest.mark.asyncio
    async def test_circular_dependency_indirect(self, db_session, validation_service, sample_bachelor_track):
        """Test detection of indirect circular dependency (A -> B -> C -> A)"""
        # Create semester
        s1 = Semester(academic_track_id=sample_bachelor_track.id, name="S1", semester_number=1)
        db_session.add(s1)
        db_session.commit()
        
        # Create courses
        courseA = Course(semester_id=s1.id, name="Course A", ects_credits=6, coefficient=1.0, difficulty_level=1)
        courseB = Course(semester_id=s1.id, name="Course B", ects_credits=6, coefficient=1.0, difficulty_level=1)
        courseC = Course(semester_id=s1.id, name="Course C", ects_credits=6, coefficient=1.0, difficulty_level=1)
        db_session.add_all([courseA, courseB, courseC])
        db_session.commit()
        
        # Create chain: B requires A, C requires B
        courseB.prerequisites.append(courseA)
        courseC.prerequisites.append(courseB)
        db_session.commit()
        
        # Try to add: A requires C (creates cycle A -> B -> C -> A)
        is_valid, error_msg = await validation_service.validate_prerequisite_chain(
            db_session, courseA.id, courseC.id
        )
        
        assert is_valid is False
        assert error_msg is not None
        assert "Circular dependency detected" in error_msg
    
    @pytest.mark.asyncio
    async def test_prerequisite_from_later_semester_rejected(self, db_session, validation_service, sample_bachelor_track):
        """Test that prerequisite from later semester is rejected"""
        # Create semesters
        s1 = Semester(academic_track_id=sample_bachelor_track.id, name="S1", semester_number=1)
        s3 = Semester(academic_track_id=sample_bachelor_track.id, name="S3", semester_number=3)
        db_session.add_all([s1, s3])
        db_session.commit()
        
        # Create courses
        course1 = Course(semester_id=s1.id, name="Early Course", ects_credits=6, coefficient=1.0, difficulty_level=1)
        course3 = Course(semester_id=s3.id, name="Advanced Course", ects_credits=6, coefficient=1.0, difficulty_level=3)
        db_session.add_all([course1, course3])
        db_session.commit()
        
        # Try to add: course1 (S1) requires course3 (S3) - should fail
        is_valid, error_msg = await validation_service.validate_prerequisite_chain(
            db_session, course1.id, course3.id
        )
        
        assert is_valid is False
        assert error_msg is not None
        assert "cannot be a prerequisite" in error_msg.lower()
        assert "earlier or same semester" in error_msg.lower()


class TestECTSHierarchyValidation:
    """Test ECTS requirements hierarchy validation"""
    
    @pytest.mark.asyncio
    async def test_valid_ects_hierarchy(self, db_session, validation_service, sample_bachelor_track):
        """Test valid ECTS hierarchy: 180 >= 120 >= 30"""
        # Create validation rules
        semester_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.SEMESTER_VALIDATION,
            name="Semester Validation",
            minimum_ects=30
        )
        year_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.YEAR_PROGRESSION,
            name="Year Progression",
            minimum_ects=60
        )
        graduation_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.GRADUATION,
            name="Graduation",
            minimum_ects=180
        )
        db_session.add_all([semester_rule, year_rule, graduation_rule])
        db_session.commit()
        
        # Validate
        is_valid, details = await validation_service.validate_ects_totals(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is True
        assert details["graduation_ects"] == 180
        assert details["year_progression_ects"] == 60
        assert details["semester_validation_ects"] == 30
        assert len(details["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_graduation_less_than_year(self, db_session, validation_service, sample_bachelor_track):
        """Test invalid hierarchy: graduation < year_progression"""
        # Create invalid rules
        year_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.YEAR_PROGRESSION,
            name="Year Progression",
            minimum_ects=120
        )
        graduation_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.GRADUATION,
            name="Graduation",
            minimum_ects=100  # Invalid: less than year_progression
        )
        db_session.add_all([year_rule, graduation_rule])
        db_session.commit()
        
        # Validate
        is_valid, details = await validation_service.validate_ects_totals(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is False
        assert len(details["errors"]) > 0
        assert any("Graduation ECTS" in error and "Year Progression ECTS" in error 
                   for error in details["errors"])
    
    @pytest.mark.asyncio
    async def test_invalid_year_less_than_semester(self, db_session, validation_service, sample_bachelor_track):
        """Test invalid hierarchy: year_progression < semester_validation"""
        # Create invalid rules
        semester_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.SEMESTER_VALIDATION,
            name="Semester Validation",
            minimum_ects=60
        )
        year_rule = ValidationRule(
            academic_track_id=sample_bachelor_track.id,
            rule_type=RuleType.YEAR_PROGRESSION,
            name="Year Progression",
            minimum_ects=50  # Invalid: less than semester_validation
        )
        db_session.add_all([semester_rule, year_rule])
        db_session.commit()
        
        # Validate
        is_valid, details = await validation_service.validate_ects_totals(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is False
        assert len(details["errors"]) > 0
        assert any("Year Progression ECTS" in error and "Semester Validation ECTS" in error 
                   for error in details["errors"])


class TestSemesterStructureValidation:
    """Test semester structure validation for Bachelor and Master tracks"""
    
    @pytest.mark.asyncio
    async def test_valid_bachelor_structure(self, db_session, validation_service, sample_bachelor_track):
        """Test valid Bachelor structure with S1-S6"""
        # Create semesters 1-6
        for i in range(1, 7):
            semester = Semester(
                academic_track_id=sample_bachelor_track.id,
                name=f"S{i}",
                semester_number=i
            )
            db_session.add(semester)
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is True
        assert len([e for e in errors if not e.startswith("Warning:")]) == 0
    
    @pytest.mark.asyncio
    async def test_valid_master_structure(self, db_session, validation_service, sample_master_track):
        """Test valid Master structure with S1-S4"""
        # Create semesters 1-4
        for i in range(1, 5):
            semester = Semester(
                academic_track_id=sample_master_track.id,
                name=f"S{i}",
                semester_number=i
            )
            db_session.add(semester)
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_master_track.id
        )
        
        assert is_valid is True
        assert len([e for e in errors if not e.startswith("Warning:")]) == 0
    
    @pytest.mark.asyncio
    async def test_bachelor_with_invalid_semester_number(self, db_session, validation_service, sample_bachelor_track):
        """Test Bachelor with semester number > 6"""
        # Create semester with invalid number
        semester = Semester(
            academic_track_id=sample_bachelor_track.id,
            name="S7",
            semester_number=7  # Invalid for Bachelor
        )
        db_session.add(semester)
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid semester_number" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_master_with_invalid_semester_number(self, db_session, validation_service, sample_master_track):
        """Test Master with semester number > 4"""
        # Create semester with invalid number
        semester = Semester(
            academic_track_id=sample_master_track.id,
            name="S5",
            semester_number=5  # Invalid for Master
        )
        db_session.add(semester)
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_master_track.id
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid semester_number" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_duplicate_semester_numbers(self, db_session, validation_service, sample_bachelor_track):
        """Test detection of duplicate semester numbers"""
        # Create duplicate semesters
        semester1 = Semester(
            academic_track_id=sample_bachelor_track.id,
            name="S1",
            semester_number=1
        )
        semester2 = Semester(
            academic_track_id=sample_bachelor_track.id,
            name="S1-Duplicate",
            semester_number=1  # Duplicate
        )
        db_session.add_all([semester1, semester2])
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_bachelor_track.id
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Duplicate semester numbers" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_missing_semesters_warning(self, db_session, validation_service, sample_bachelor_track):
        """Test warning for missing semesters in sequence"""
        # Create only S1 and S3 (missing S2)
        semester1 = Semester(academic_track_id=sample_bachelor_track.id, name="S1", semester_number=1)
        semester3 = Semester(academic_track_id=sample_bachelor_track.id, name="S3", semester_number=3)
        db_session.add_all([semester1, semester3])
        db_session.commit()
        
        # Validate
        is_valid, errors = await validation_service.validate_semester_structure(
            db_session, sample_bachelor_track.id
        )
        
        # Should have warnings but still be valid
        assert any("Warning" in error or "missing semester numbers" in error for error in errors)


class TestImportDataValidation:
    """Test import data validation"""
    
    @pytest.mark.asyncio
    async def test_valid_import_data(self, validation_service):
        """Test validation of complete valid import data"""
        import_data = {
            "universities": [
                {"name": "Test University", "country": "Germany"}
            ],
            "programs": [
                {"name": "Computer Science"}
            ],
            "tracks": [
                {
                    "name": "Bachelor CS",
                    "level": "bachelor",
                    "total_ects_required": 180
                }
            ],
            "semesters": [
                {"name": "S1", "semester_number": 1}
            ],
            "courses": [
                {
                    "name": "Intro to Programming",
                    "ects_credits": 6,
                    "coefficient": 1.0,
                    "difficulty_level": 2
                }
            ]
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_missing_required_keys(self, validation_service):
        """Test detection of missing required keys"""
        import_data = {
            "universities": []
            # Missing programs, tracks, semesters, courses
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required key" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_ects_credits(self, validation_service):
        """Test detection of invalid ECTS credits (must be 1-30)"""
        import_data = {
            "universities": [{"name": "Test", "country": "Germany"}],
            "programs": [{"name": "CS"}],
            "tracks": [{"name": "Bachelor", "level": "bachelor", "total_ects_required": 180}],
            "semesters": [{"name": "S1", "semester_number": 1}],
            "courses": [
                {
                    "name": "Invalid Course",
                    "ects_credits": 35,  # Invalid: > 30
                    "coefficient": 1.0,
                    "difficulty_level": 2
                }
            ]
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is False
        assert any("ects_credits" in error and "between 1 and 30" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_coefficient(self, validation_service):
        """Test detection of invalid coefficient (must be 0.1-10.0)"""
        import_data = {
            "universities": [{"name": "Test", "country": "Germany"}],
            "programs": [{"name": "CS"}],
            "tracks": [{"name": "Bachelor", "level": "bachelor", "total_ects_required": 180}],
            "semesters": [{"name": "S1", "semester_number": 1}],
            "courses": [
                {
                    "name": "Invalid Course",
                    "ects_credits": 6,
                    "coefficient": 15.0,  # Invalid: > 10.0
                    "difficulty_level": 2
                }
            ]
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is False
        assert any("coefficient" in error and "between 0.1 and 10.0" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_difficulty_level(self, validation_service):
        """Test detection of invalid difficulty level (must be 1-5)"""
        import_data = {
            "universities": [{"name": "Test", "country": "Germany"}],
            "programs": [{"name": "CS"}],
            "tracks": [{"name": "Bachelor", "level": "bachelor", "total_ects_required": 180}],
            "semesters": [{"name": "S1", "semester_number": 1}],
            "courses": [
                {
                    "name": "Invalid Course",
                    "ects_credits": 6,
                    "coefficient": 1.0,
                    "difficulty_level": 6  # Invalid: > 5
                }
            ]
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is False
        assert any("difficulty_level" in error and "between 1 and 5" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_track_level(self, validation_service):
        """Test detection of invalid track level"""
        import_data = {
            "universities": [{"name": "Test", "country": "Germany"}],
            "programs": [{"name": "CS"}],
            "tracks": [
                {
                    "name": "Invalid Track",
                    "level": "undergraduate",  # Invalid: must be bachelor/master/doctorate
                    "total_ects_required": 180
                }
            ],
            "semesters": [{"name": "S1", "semester_number": 1}],
            "courses": [{"name": "Course", "ects_credits": 6, "coefficient": 1.0, "difficulty_level": 2}]
        }
        
        is_valid, errors = await validation_service.validate_import_data(import_data)
        
        assert is_valid is False
        assert any("invalid level" in error for error in errors)
