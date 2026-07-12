"""
Tests for curriculum schemas validation
"""
import pytest
from pydantic import ValidationError
from app.schemas.curriculum import (
    CourseCreate,
    CourseUpdate,
    SemesterCreate,
    TeachingUnitCreate,
    AcademicTrackCreate,
    TrackLevel,
)


class TestCourseSchemas:
    """Tests for Course schemas"""
    
    def test_course_create_valid(self):
        """Test creating a valid course"""
        course = CourseCreate(
            semester_id=1,
            name="Introduction to Computer Science",
            name_de="Einführung in die Informatik",
            code="CS101",
            ects_credits=6,
            coefficient=1.5,
            difficulty_level=3
        )
        assert course.ects_credits == 6
        assert course.coefficient == 1.5
        assert course.difficulty_level == 3
    
    def test_course_ects_validation(self):
        """Test ECTS validation (1-30 range)"""
        # Valid ECTS values
        course = CourseCreate(
            semester_id=1,
            name="Test Course",
            ects_credits=1,
            coefficient=1.0,
            difficulty_level=3
        )
        assert course.ects_credits == 1
        
        course = CourseCreate(
            semester_id=1,
            name="Test Course",
            ects_credits=30,
            coefficient=1.0,
            difficulty_level=3
        )
        assert course.ects_credits == 30
        
        # Invalid ECTS: below minimum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=0,
                coefficient=1.0,
                difficulty_level=3
            )
        assert "ects_credits" in str(exc_info.value)
        
        # Invalid ECTS: above maximum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=31,
                coefficient=1.0,
                difficulty_level=3
            )
        assert "ects_credits" in str(exc_info.value)
    
    def test_course_coefficient_validation(self):
        """Test coefficient validation (0.1-10.0 range)"""
        # Valid coefficient values
        course = CourseCreate(
            semester_id=1,
            name="Test Course",
            ects_credits=6,
            coefficient=0.1,
            difficulty_level=3
        )
        assert course.coefficient == 0.1
        
        course = CourseCreate(
            semester_id=1,
            name="Test Course",
            ects_credits=6,
            coefficient=10.0,
            difficulty_level=3
        )
        assert course.coefficient == 10.0
        
        # Invalid coefficient: below minimum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=6,
                coefficient=0.05,
                difficulty_level=3
            )
        assert "coefficient" in str(exc_info.value)
        
        # Invalid coefficient: above maximum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=6,
                coefficient=10.5,
                difficulty_level=3
            )
        assert "coefficient" in str(exc_info.value)
    
    def test_course_difficulty_validation(self):
        """Test difficulty validation (1-5 range)"""
        # Valid difficulty values
        for difficulty in [1, 2, 3, 4, 5]:
            course = CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=6,
                coefficient=1.0,
                difficulty_level=difficulty
            )
            assert course.difficulty_level == difficulty
        
        # Invalid difficulty: below minimum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=6,
                coefficient=1.0,
                difficulty_level=0
            )
        assert "difficulty_level" in str(exc_info.value)
        
        # Invalid difficulty: above maximum
        with pytest.raises(ValidationError) as exc_info:
            CourseCreate(
                semester_id=1,
                name="Test Course",
                ects_credits=6,
                coefficient=1.0,
                difficulty_level=6
            )
        assert "difficulty_level" in str(exc_info.value)
    
    def test_course_update_optional_fields(self):
        """Test that all fields are optional in CourseUpdate"""
        update = CourseUpdate()
        assert update.name is None
        assert update.ects_credits is None
        
        # Update with only some fields
        update = CourseUpdate(ects_credits=12, difficulty_level=4)
        assert update.ects_credits == 12
        assert update.difficulty_level == 4
        assert update.name is None


class TestSemesterSchemas:
    """Tests for Semester schemas"""
    
    def test_semester_create_valid(self):
        """Test creating a valid semester"""
        semester = SemesterCreate(
            academic_track_id=1,
            name="S1",
            name_de="Semester 1",
            semester_number=1,
            ects_required=30
        )
        assert semester.semester_number == 1
        assert semester.ects_required == 30
    
    def test_semester_number_validation(self):
        """Test semester number validation (1-10 range)"""
        # Valid semester numbers
        semester = SemesterCreate(
            academic_track_id=1,
            name="S1",
            semester_number=1
        )
        assert semester.semester_number == 1
        
        semester = SemesterCreate(
            academic_track_id=1,
            name="S10",
            semester_number=10
        )
        assert semester.semester_number == 10
        
        # Invalid: below minimum
        with pytest.raises(ValidationError) as exc_info:
            SemesterCreate(
                academic_track_id=1,
                name="S0",
                semester_number=0
            )
        assert "semester_number" in str(exc_info.value)
        
        # Invalid: above maximum
        with pytest.raises(ValidationError) as exc_info:
            SemesterCreate(
                academic_track_id=1,
                name="S11",
                semester_number=11
            )
        assert "semester_number" in str(exc_info.value)


class TestTeachingUnitSchemas:
    """Tests for Teaching Unit schemas"""
    
    def test_teaching_unit_create_valid(self):
        """Test creating a valid teaching unit"""
        unit = TeachingUnitCreate(
            semester_id=1,
            name="Fundamental Computer Science",
            name_de="Grundlegende Informatik",
            code="UE1",
            ects_required=15
        )
        assert unit.name == "Fundamental Computer Science"
        assert unit.code == "UE1"
        assert unit.ects_required == 15


class TestAcademicTrackSchemas:
    """Tests for Academic Track schemas"""
    
    def test_academic_track_create_valid(self):
        """Test creating a valid academic track"""
        track = AcademicTrackCreate(
            study_program_id=1,
            name="Bachelor of Computer Science",
            name_de="Bachelor Informatik",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        assert track.level == TrackLevel.BACHELOR
        assert track.total_ects_required == 180
    
    def test_academic_track_ects_validation(self):
        """Test total ECTS must be positive"""
        # Valid ECTS
        track = AcademicTrackCreate(
            study_program_id=1,
            name="Bachelor of Computer Science",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        assert track.total_ects_required == 180
        
        # Invalid: zero or negative
        with pytest.raises(ValidationError) as exc_info:
            AcademicTrackCreate(
                study_program_id=1,
                name="Bachelor of Computer Science",
                level=TrackLevel.BACHELOR,
                total_ects_required=0
            )
        assert "total_ects_required" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AcademicTrackCreate(
                study_program_id=1,
                name="Bachelor of Computer Science",
                level=TrackLevel.BACHELOR,
                total_ects_required=-10
            )
        assert "total_ects_required" in str(exc_info.value)
    
    def test_academic_track_level_enum(self):
        """Test academic track level enum values"""
        # Valid enum values
        for level in [TrackLevel.BACHELOR, TrackLevel.MASTER, TrackLevel.DOCTORATE]:
            track = AcademicTrackCreate(
                study_program_id=1,
                name="Test Track",
                level=level,
                total_ects_required=180
            )
            assert track.level == level
        
        # Invalid enum value
        with pytest.raises(ValidationError) as exc_info:
            AcademicTrackCreate(
                study_program_id=1,
                name="Test Track",
                level="invalid_level",
                total_ects_required=180
            )
        assert "level" in str(exc_info.value)
