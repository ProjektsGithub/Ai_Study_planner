"""
Tests for academic entity models (University, Campus, StudyProgram, AcademicTrack, etc.)
"""
import pytest
from datetime import datetime, timezone
from app.models import (
    University,
    Campus,
    StudyProgram,
    AcademicTrack,
    TrackLevel,
    Semester,
    TeachingUnit,
    Course,
    ValidationRule,
    RuleType,
)


def test_university_model():
    """Test University model instantiation"""
    university = University(
        name="Technical University of Munich",
        name_de="Technische Universität München",
        country="Germany",
        description="A leading technical university",
        description_de="Eine führende technische Universität",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert university.name == "Technical University of Munich"
    assert university.name_de == "Technische Universität München"
    assert university.country == "Germany"
    assert university.is_deleted is False


def test_campus_model():
    """Test Campus model instantiation"""
    campus = Campus(
        university_id=1,
        name="Main Campus",
        name_de="Hauptcampus",
        location="Munich",
        description="Main campus in Munich",
        description_de="Hauptcampus in München",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert campus.name == "Main Campus"
    assert campus.name_de == "Hauptcampus"
    assert campus.location == "Munich"
    assert campus.university_id == 1
    assert campus.is_deleted is False


def test_study_program_model():
    """Test StudyProgram model instantiation"""
    program = StudyProgram(
        name="Computer Science",
        name_de="Informatik",
        code="CS",
        description="Computer Science program",
        description_de="Informatik Studiengang",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert program.name == "Computer Science"
    assert program.name_de == "Informatik"
    assert program.code == "CS"
    assert program.is_deleted is False


def test_academic_track_model():
    """Test AcademicTrack model instantiation"""
    track = AcademicTrack(
        study_program_id=1,
        name="Bachelor in Computer Science",
        name_de="Bachelor Informatik",
        level=TrackLevel.BACHELOR,
        total_ects_required=180,
        graduation_conditions="Complete all required courses and thesis",
        graduation_conditions_de="Alle erforderlichen Kurse und Abschlussarbeit abschließen",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert track.name == "Bachelor in Computer Science"
    assert track.level == TrackLevel.BACHELOR
    assert track.total_ects_required == 180
    assert track.is_deleted is False


def test_semester_model():
    """Test Semester model instantiation"""
    semester = Semester(
        academic_track_id=1,
        name="S1",
        name_de="Semester 1",
        semester_number=1,
        ects_required=30,
        description="First semester",
        description_de="Erstes Semester",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert semester.name == "S1"
    assert semester.semester_number == 1
    assert semester.ects_required == 30
    assert semester.is_deleted is False


def test_teaching_unit_model():
    """Test TeachingUnit model instantiation"""
    teaching_unit = TeachingUnit(
        semester_id=1,
        name="Fundamentals of Programming",
        name_de="Grundlagen der Programmierung",
        code="UE1",
        ects_required=12,
        description="Programming fundamentals",
        description_de="Grundlagen der Programmierung",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert teaching_unit.name == "Fundamentals of Programming"
    assert teaching_unit.code == "UE1"
    assert teaching_unit.ects_required == 12
    assert teaching_unit.is_deleted is False


def test_course_model():
    """Test Course model instantiation"""
    course = Course(
        teaching_unit_id=1,
        semester_id=1,
        name="Introduction to Python",
        name_de="Einführung in Python",
        code="CS101",
        ects_credits=6,
        coefficient=1.5,
        difficulty_level=2,
        description="Introduction to Python programming",
        description_de="Einführung in die Python-Programmierung",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert course.name == "Introduction to Python"
    assert course.code == "CS101"
    assert course.ects_credits == 6
    assert course.coefficient == 1.5
    assert course.difficulty_level == 2
    assert course.is_deleted is False


def test_validation_rule_model():
    """Test ValidationRule model instantiation"""
    rule = ValidationRule(
        academic_track_id=1,
        rule_type=RuleType.SEMESTER_VALIDATION,
        name="Semester 1 Validation",
        name_de="Semester 1 Validierung",
        minimum_ects=24,
        description="Minimum ECTS for semester validation",
        description_de="Mindest-ECTS für Semestervalidierung",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert rule.rule_type == RuleType.SEMESTER_VALIDATION
    assert rule.minimum_ects == 24
    assert rule.name == "Semester 1 Validation"
    assert rule.is_deleted is False


def test_track_level_enum():
    """Test TrackLevel enum values"""
    assert TrackLevel.BACHELOR == "bachelor"
    assert TrackLevel.MASTER == "master"
    assert TrackLevel.DOCTORATE == "doctorate"


def test_rule_type_enum():
    """Test RuleType enum values"""
    assert RuleType.SEMESTER_VALIDATION == "semester_validation"
    assert RuleType.YEAR_PROGRESSION == "year_progression"
    assert RuleType.GRADUATION == "graduation"
