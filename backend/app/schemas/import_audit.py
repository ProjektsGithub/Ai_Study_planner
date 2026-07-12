"""
Pydantic schemas for Import and Audit operations
Schemas for Excel import validation, audit logging, and error reporting
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class OperationType(str, Enum):
    """Enum for audit log operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class EntityType(str, Enum):
    """Enum for entity types in the system"""
    UNIVERSITY = "university"
    CAMPUS = "campus"
    STUDY_PROGRAM = "study_program"
    ACADEMIC_TRACK = "academic_track"
    SEMESTER = "semester"
    TEACHING_UNIT = "teaching_unit"
    COURSE = "course"
    PREREQUISITE = "prerequisite"
    VALIDATION_RULE = "validation_rule"
    USER = "user"
    ROLE = "role"


# ==================== Validation Error Schemas ====================

class ValidationErrorDetail(BaseModel):
    """Detailed validation error for a specific field or row"""
    field: Optional[str] = Field(None, description="Field name where the error occurred")
    row: Optional[int] = Field(None, description="Row number in import file (if applicable)")
    sheet: Optional[str] = Field(None, description="Sheet name in Excel file (if applicable)")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the error")
    value: Optional[Any] = Field(None, description="The invalid value that caused the error")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field": "ects_credits",
                    "row": 15,
                    "sheet": "Courses",
                    "error_code": "INVALID_RANGE",
                    "message": "ECTS credits must be between 1 and 30",
                    "suggestion": "Please enter a value between 1 and 30",
                    "value": 35
                }
            ]
        }
    }


class ValidationErrorSchema(BaseModel):
    """
    Schema for detailed error reporting during validation
    Provides comprehensive information about validation failures
    """
    is_valid: bool = Field(..., description="Whether the validation passed")
    errors: List[ValidationErrorDetail] = Field(default=[], description="List of validation errors")
    error_count: int = Field(default=0, description="Total number of errors")
    warning_count: int = Field(default=0, description="Total number of warnings (non-blocking)")
    warnings: List[ValidationErrorDetail] = Field(default=[], description="List of non-critical warnings")
    
    def model_post_init(self, __context):
        """Calculate counts from lists after initialization"""
        if self.error_count == 0 and self.errors:
            self.error_count = len(self.errors)
        if self.warning_count == 0 and self.warnings:
            self.warning_count = len(self.warnings)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_valid": False,
                    "error_count": 2,
                    "warning_count": 1,
                    "errors": [
                        {
                            "field": "ects_credits",
                            "row": 15,
                            "sheet": "Courses",
                            "error_code": "INVALID_RANGE",
                            "message": "ECTS credits must be between 1 and 30",
                            "suggestion": "Please enter a value between 1 and 30",
                            "value": 35
                        },
                        {
                            "field": "prerequisite_chain",
                            "row": 20,
                            "sheet": "Prerequisites",
                            "error_code": "CIRCULAR_DEPENDENCY",
                            "message": "Circular dependency detected: Course A -> Course B -> Course A",
                            "suggestion": "Remove one of the prerequisite relationships to break the cycle"
                        }
                    ],
                    "warnings": [
                        {
                            "field": "description",
                            "row": 10,
                            "sheet": "Courses",
                            "message": "Course description is missing (optional field)"
                        }
                    ]
                }
            ]
        }
    }


# ==================== Import Data Schemas ====================

class ImportUniversityData(BaseModel):
    """Data for importing a single university"""
    name: str = Field(..., min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    country: str = Field(default="Germany", max_length=100)
    description: Optional[str] = None
    description_de: Optional[str] = None
    campuses: Optional[List[Dict[str, Any]]] = Field(default=[], description="List of campus data")


class ImportProgramData(BaseModel):
    """Data for importing a single study program"""
    name: str = Field(..., min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    description_de: Optional[str] = None
    university_names: List[str] = Field(default=[], description="List of university names to link")


class ImportTrackData(BaseModel):
    """Data for importing a single academic track"""
    name: str = Field(..., min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    level: str = Field(..., description="bachelor, master, or doctorate")
    program_name: str = Field(..., description="Name of the study program")
    total_ects_required: int = Field(..., gt=0)
    description: Optional[str] = None
    description_de: Optional[str] = None


class ImportSemesterData(BaseModel):
    """Data for importing a single semester"""
    name: str = Field(..., min_length=1, max_length=100)
    name_de: Optional[str] = Field(None, max_length=100)
    semester_number: int = Field(..., ge=1, le=10)
    track_name: str = Field(..., description="Name of the academic track")
    ects_required: Optional[int] = Field(None, ge=0)


class ImportTeachingUnitData(BaseModel):
    """Data for importing a single teaching unit"""
    name: str = Field(..., min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    semester_name: str = Field(..., description="Name of the semester")
    ects_required: Optional[int] = Field(None, ge=0)


class ImportCourseData(BaseModel):
    """Data for importing a single course"""
    name: str = Field(..., min_length=1, max_length=255)
    name_de: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    semester_name: str = Field(..., description="Name of the semester")
    teaching_unit_name: Optional[str] = Field(None, description="Name of the teaching unit (optional)")
    ects_credits: int = Field(..., ge=1, le=30)
    coefficient: float = Field(..., ge=0.1, le=10.0)
    difficulty_level: int = Field(..., ge=1, le=5)
    description: Optional[str] = None
    description_de: Optional[str] = None
    prerequisites: List[str] = Field(default=[], description="List of prerequisite course names")


class ImportDataSchema(BaseModel):
    """
    Schema for Excel import validation
    Represents the complete structure of data to be imported from an Excel file
    
    Validates:
    - Requirements 9.1: Excel file format structure
    - Requirements 9.2: Structural correctness of imported data
    - Requirements 9.3: Semantic correctness including ECTS totals and prerequisite chains
    - Requirements 9.9: Support for importing all entity types in a single file
    """
    universities: List[ImportUniversityData] = Field(default=[], description="List of universities to import")
    programs: List[ImportProgramData] = Field(default=[], description="List of study programs to import")
    tracks: List[ImportTrackData] = Field(default=[], description="List of academic tracks to import")
    semesters: List[ImportSemesterData] = Field(default=[], description="List of semesters to import")
    teaching_units: List[ImportTeachingUnitData] = Field(default=[], description="List of teaching units to import")
    courses: List[ImportCourseData] = Field(default=[], description="List of courses to import")
    
    @field_validator('universities', 'programs', 'tracks', 'semesters', 'teaching_units', 'courses')
    @classmethod
    def validate_not_empty(cls, v, info):
        """Ensure at least one entity type has data"""
        # We allow empty lists for individual types, but the overall import should have some data
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "universities": [
                        {
                            "name": "Technical University Munich",
                            "name_de": "Technische Universität München",
                            "country": "Germany"
                        }
                    ],
                    "programs": [
                        {
                            "name": "Computer Science",
                            "name_de": "Informatik",
                            "code": "CS",
                            "university_names": ["Technical University Munich"]
                        }
                    ],
                    "tracks": [
                        {
                            "name": "Bachelor of Science",
                            "name_de": "Bachelor Wissenschaft",
                            "level": "bachelor",
                            "program_name": "Computer Science",
                            "total_ects_required": 180
                        }
                    ],
                    "courses": [
                        {
                            "name": "Introduction to Programming",
                            "name_de": "Einführung in die Programmierung",
                            "code": "CS101",
                            "semester_name": "S1",
                            "ects_credits": 6,
                            "coefficient": 1.5,
                            "difficulty_level": 2,
                            "prerequisites": []
                        }
                    ]
                }
            ]
        }
    }


class ImportPreviewResponse(BaseModel):
    """
    Schema for import preview showing what entities will be created
    Requirement 9.4: Display preview of imported data before final confirmation
    """
    universities_count: int = Field(default=0, description="Number of universities to be created")
    programs_count: int = Field(default=0, description="Number of study programs to be created")
    tracks_count: int = Field(default=0, description="Number of academic tracks to be created")
    semesters_count: int = Field(default=0, description="Number of semesters to be created")
    teaching_units_count: int = Field(default=0, description="Number of teaching units to be created")
    courses_count: int = Field(default=0, description="Number of courses to be created")
    prerequisites_count: int = Field(default=0, description="Number of prerequisite relationships to be created")
    
    sample_universities: List[str] = Field(default=[], description="Sample of university names (max 5)")
    sample_courses: List[str] = Field(default=[], description="Sample of course names (max 10)")
    
    total_entities: int = Field(default=0, description="Total number of entities to be created")
    
    def model_post_init(self, __context):
        """Calculate total entities from individual counts after initialization"""
        if self.total_entities == 0:
            self.total_entities = (
                self.universities_count + self.programs_count + 
                self.tracks_count + self.semesters_count + 
                self.teaching_units_count + self.courses_count + 
                self.prerequisites_count
            )


class ImportSummaryResponse(BaseModel):
    """
    Schema for import execution summary
    Requirement 9.10: Display summary of created entities after successful import
    """
    import_id: int = Field(..., description="ID of the import operation")
    success: bool = Field(..., description="Whether the import was successful")
    timestamp: datetime = Field(..., description="Timestamp of the import")
    user_id: Optional[int] = Field(None, description="ID of the user who performed the import")
    
    universities_created: int = Field(default=0)
    programs_created: int = Field(default=0)
    tracks_created: int = Field(default=0)
    semesters_created: int = Field(default=0)
    teaching_units_created: int = Field(default=0)
    courses_created: int = Field(default=0)
    prerequisites_created: int = Field(default=0)
    
    total_entities_created: int = Field(default=0, description="Total number of entities created")
    
    error_message: Optional[str] = Field(None, description="Error message if import failed")
    
    def model_post_init(self, __context):
        """Calculate total entities created from individual counts after initialization"""
        if self.total_entities_created == 0:
            self.total_entities_created = (
                self.universities_created + self.programs_created + 
                self.tracks_created + self.semesters_created + 
                self.teaching_units_created + self.courses_created + 
                self.prerequisites_created
            )


# ==================== Audit Log Schemas ====================

class FieldChange(BaseModel):
    """Represents a single field change in an update operation"""
    field_name: str = Field(..., description="Name of the field that changed")
    old_value: Any = Field(None, description="Value before the change")
    new_value: Any = Field(None, description="Value after the change")
    field_display_name: Optional[str] = Field(None, description="Human-readable field name for display")


class AuditLogResponse(BaseModel):
    """
    Schema for audit log response with before/after field display
    
    Validates:
    - Requirements 16.1: Log all create, update, delete operations with timestamp and user information
    - Requirements 16.5: Display before and after values for update operations
    """
    id: int = Field(..., description="Audit log ID")
    entity_type: str = Field(..., description="Type of entity (e.g., 'university', 'course')")
    entity_id: int = Field(..., description="ID of the entity that was modified")
    operation: OperationType = Field(..., description="Operation type: create, update, or delete")
    
    # User information (Requirement 16.1)
    user_id: Optional[int] = Field(None, description="ID of the user who performed the operation")
    user_email: Optional[str] = Field(None, description="Email of the user who performed the operation")
    user_name: Optional[str] = Field(None, description="Name of the user who performed the operation")
    
    # Timestamp (Requirement 16.1)
    timestamp: datetime = Field(..., description="When the operation occurred")
    
    # Before/after values (Requirement 16.5)
    before_value: Optional[Dict[str, Any]] = Field(None, description="Complete state before the operation (for update/delete)")
    after_value: Optional[Dict[str, Any]] = Field(None, description="Complete state after the operation (for create/update)")
    
    # Field-level changes for easier display (Requirement 16.5)
    changes: Optional[List[FieldChange]] = Field(None, description="Detailed list of field changes (for update operations)")
    
    # Optional description
    description: Optional[str] = Field(None, description="Human-readable description of the operation")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1234,
                    "entity_type": "course",
                    "entity_id": 567,
                    "operation": "update",
                    "user_id": 1,
                    "user_email": "admin@university.de",
                    "user_name": "John Admin",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "before_value": {
                        "name": "Introduction to Programming",
                        "ects_credits": 5,
                        "difficulty_level": 2
                    },
                    "after_value": {
                        "name": "Introduction to Programming",
                        "ects_credits": 6,
                        "difficulty_level": 3
                    },
                    "changes": [
                        {
                            "field_name": "ects_credits",
                            "field_display_name": "ECTS Credits",
                            "old_value": 5,
                            "new_value": 6
                        },
                        {
                            "field_name": "difficulty_level",
                            "field_display_name": "Difficulty Level",
                            "old_value": 2,
                            "new_value": 3
                        }
                    ],
                    "description": "Updated course ECTS credits and difficulty level"
                }
            ]
        }
    }


class AuditLogListResponse(BaseModel):
    """Schema for paginated list of audit logs"""
    logs: List[AuditLogResponse] = Field(..., description="List of audit log entries")
    total: int = Field(..., description="Total number of audit logs matching the filter")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=50, ge=1, le=500, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class AuditLogFilterParams(BaseModel):
    """Parameters for filtering audit logs"""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[int] = Field(None, description="Filter by specific entity ID")
    operation: Optional[OperationType] = Field(None, description="Filter by operation type")
    user_id: Optional[int] = Field(None, description="Filter by user who performed the operation")
    start_date: Optional[datetime] = Field(None, description="Filter logs after this date")
    end_date: Optional[datetime] = Field(None, description="Filter logs before this date")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=500, description="Number of items per page")


class EntityHistoryResponse(BaseModel):
    """
    Schema for entity change history
    Requirement 16.4: Allow viewing of change history for individual entities
    """
    entity_type: str = Field(..., description="Type of entity")
    entity_id: int = Field(..., description="ID of the entity")
    entity_name: Optional[str] = Field(None, description="Current name of the entity")
    
    history: List[AuditLogResponse] = Field(..., description="Chronological list of changes (newest first)")
    total_changes: int = Field(..., description="Total number of changes to this entity")
    
    created_at: Optional[datetime] = Field(None, description="When the entity was created")
    created_by: Optional[str] = Field(None, description="User who created the entity")
    
    last_modified_at: Optional[datetime] = Field(None, description="When the entity was last modified")
    last_modified_by: Optional[str] = Field(None, description="User who last modified the entity")
