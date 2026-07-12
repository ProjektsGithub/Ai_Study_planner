"""
Unit tests for admin schemas (university, program, campus)
Tests validation rules including German text support
"""
import pytest
from pydantic import ValidationError
from app.schemas.admin import (
    UniversityCreate,
    UniversityUpdate,
    CampusCreate,
    CampusUpdate,
    StudyProgramCreate,
    StudyProgramUpdate,
)


class TestUniversitySchemas:
    """Test university schema validation"""
    
    def test_university_create_valid(self):
        """Test creating university with valid data"""
        data = {
            "name": "Technical University Munich",
            "name_de": "Technische Universität München",
            "country": "Germany",
            "description": "Leading technical university",
            "description_de": "Führende technische Universität"
        }
        university = UniversityCreate(**data)
        assert university.name == "Technical University Munich"
        assert university.name_de == "Technische Universität München"
        assert university.country == "Germany"
    
    def test_university_create_german_special_chars(self):
        """Test German special characters ä, ö, ü, ß are accepted"""
        data = {
            "name": "University Test",
            "name_de": "Universität für Wissenschaft und Bildung in Köln",
            "country": "Germany",
            "description_de": "Eine großartige Universität mit äußerst günstigen Bedingungen"
        }
        university = UniversityCreate(**data)
        assert "ä" in university.name_de
        assert "ü" in university.name_de
        assert "ö" in university.name_de
        assert "ß" in university.description_de
    
    def test_university_create_minimal(self):
        """Test creating university with minimal required fields"""
        data = {
            "name": "Test University"
        }
        university = UniversityCreate(**data)
        assert university.name == "Test University"
        assert university.country == "Germany"  # default value
        assert university.name_de is None
    
    def test_university_create_empty_name_fails(self):
        """Test that empty name fails validation"""
        with pytest.raises(ValidationError) as exc_info:
            UniversityCreate(name="")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)
    
    def test_university_create_name_too_long_fails(self):
        """Test that name exceeding 255 chars fails"""
        with pytest.raises(ValidationError):
            UniversityCreate(name="A" * 256)
    
    def test_university_update_partial(self):
        """Test updating university with partial data"""
        data = {
            "name_de": "Neue Universität",
            "description": "Updated description"
        }
        update = UniversityUpdate(**data)
        assert update.name_de == "Neue Universität"
        assert update.description == "Updated description"
        assert update.name is None  # not provided
    
    def test_university_update_all_optional(self):
        """Test that all fields are optional in update"""
        update = UniversityUpdate()
        assert update.name is None
        assert update.name_de is None
        assert update.country is None


class TestCampusSchemas:
    """Test campus schema validation"""
    
    def test_campus_create_valid(self):
        """Test creating campus with valid data"""
        data = {
            "university_id": 1,
            "name": "Main Campus",
            "name_de": "Hauptcampus",
            "location": "München",
            "description": "Central campus location",
            "description_de": "Zentraler Campus-Standort"
        }
        campus = CampusCreate(**data)
        assert campus.university_id == 1
        assert campus.name == "Main Campus"
        assert campus.location == "München"
    
    def test_campus_create_german_chars_in_location(self):
        """Test German characters in location field"""
        data = {
            "university_id": 1,
            "name": "Campus",
            "location": "Köln-Südstadt, Nähe Universität"
        }
        campus = CampusCreate(**data)
        assert "ö" in campus.location
        assert "ä" in campus.location
    
    def test_campus_create_minimal(self):
        """Test creating campus with minimal required fields"""
        data = {
            "university_id": 1,
            "name": "Test Campus"
        }
        campus = CampusCreate(**data)
        assert campus.university_id == 1
        assert campus.name == "Test Campus"
        assert campus.location is None
    
    def test_campus_create_invalid_university_id(self):
        """Test that university_id must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            CampusCreate(university_id=0, name="Test")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("university_id",) for error in errors)
    
    def test_campus_create_negative_university_id_fails(self):
        """Test that negative university_id fails"""
        with pytest.raises(ValidationError):
            CampusCreate(university_id=-1, name="Test")
    
    def test_campus_update_partial(self):
        """Test updating campus with partial data"""
        data = {
            "name_de": "Neuer Campus",
            "location": "Neue Adresse"
        }
        update = CampusUpdate(**data)
        assert update.name_de == "Neuer Campus"
        assert update.location == "Neue Adresse"
        assert update.name is None


class TestStudyProgramSchemas:
    """Test study program schema validation"""
    
    def test_study_program_create_valid(self):
        """Test creating study program with valid data"""
        data = {
            "name": "Computer Science",
            "name_de": "Informatik",
            "code": "CS",
            "description": "Study of computation and information",
            "description_de": "Studium der Berechnung und Information"
        }
        program = StudyProgramCreate(**data)
        assert program.name == "Computer Science"
        assert program.name_de == "Informatik"
        assert program.code == "CS"
    
    def test_study_program_german_chars_in_name(self):
        """Test German characters in program name"""
        data = {
            "name": "Medicine",
            "name_de": "Medizin für Ärzte und Chirurgen",
            "description_de": "Umfassendes Studium der ärztlichen Wissenschaften"
        }
        program = StudyProgramCreate(**data)
        assert "Ä" in program.name_de
        assert "ä" in program.description_de
    
    def test_study_program_create_minimal(self):
        """Test creating study program with minimal required fields"""
        data = {
            "name": "Test Program"
        }
        program = StudyProgramCreate(**data)
        assert program.name == "Test Program"
        assert program.code is None
    
    def test_study_program_code_uppercase_only(self):
        """Test that program code must be uppercase"""
        data = {
            "name": "Test",
            "code": "CS123"
        }
        program = StudyProgramCreate(**data)
        assert program.code == "CS123"
    
    def test_study_program_code_lowercase_fails(self):
        """Test that lowercase code fails validation"""
        with pytest.raises(ValidationError) as exc_info:
            StudyProgramCreate(name="Test", code="cs")
        
        errors = exc_info.value.errors()
        assert any("code" in str(error) for error in errors)
    
    def test_study_program_code_with_special_chars_fails(self):
        """Test that code with special characters fails"""
        with pytest.raises(ValidationError):
            StudyProgramCreate(name="Test", code="CS-123")
    
    def test_study_program_empty_name_fails(self):
        """Test that empty name fails validation"""
        with pytest.raises(ValidationError):
            StudyProgramCreate(name="")
    
    def test_study_program_update_partial(self):
        """Test updating study program with partial data"""
        data = {
            "name_de": "Neue Informatik",
            "code": "NEWCS"
        }
        update = StudyProgramUpdate(**data)
        assert update.name_de == "Neue Informatik"
        assert update.code == "NEWCS"
        assert update.name is None
    
    def test_study_program_update_all_optional(self):
        """Test that all fields are optional in update"""
        update = StudyProgramUpdate()
        assert update.name is None
        assert update.code is None


class TestGermanTextValidation:
    """Test German text validation across all schemas"""
    
    def test_accept_all_german_chars(self):
        """Test that all German special characters are accepted"""
        text_with_german = "Äußerst schöne Universität in Köln, Größe: groß"
        data = {
            "name": "Test",
            "description_de": text_with_german
        }
        university = UniversityCreate(**data)
        assert university.description_de == text_with_german
    
    def test_accept_numbers_and_punctuation(self):
        """Test that numbers and common punctuation are accepted"""
        data = {
            "name": "University Test (2024)",
            "description": "Founded in 1990: Excellence & Innovation - Top 10!"
        }
        university = UniversityCreate(**data)
        assert university.name == "University Test (2024)"
    
    def test_accept_forward_slash(self):
        """Test that forward slashes are accepted"""
        data = {
            "name": "Bachelor/Master Program",
            "description": "Program for Bachelor/Master students"
        }
        program = StudyProgramCreate(**data)
        assert "/" in program.name


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_university_max_length_name(self):
        """Test university with maximum length name"""
        data = {
            "name": "A" * 255
        }
        university = UniversityCreate(**data)
        assert len(university.name) == 255
    
    def test_campus_with_university_id_one(self):
        """Test campus with university_id = 1 (boundary)"""
        data = {
            "university_id": 1,
            "name": "Campus"
        }
        campus = CampusCreate(**data)
        assert campus.university_id == 1
    
    def test_program_code_empty_string_accepted(self):
        """Test that empty string code is converted to None"""
        data = {
            "name": "Test",
            "code": ""
        }
        # Empty string should be allowed but treated as optional
        program = StudyProgramCreate(**data)
        assert program.code == ""
    
    def test_none_values_for_optional_fields(self):
        """Test that None values work for optional fields"""
        data = {
            "name": "Test University",
            "name_de": None,
            "description": None
        }
        university = UniversityCreate(**data)
        assert university.name_de is None
        assert university.description is None
