# Import and Audit Schemas Documentation

This document describes the Pydantic schemas created for import operations and audit logging in the Super Admin Platform.

## File: `app/schemas/import_audit.py`

### Overview
Contains comprehensive schemas for:
1. **Excel Import Validation** - Validating bulk curriculum data imports
2. **Audit Logging** - Tracking administrative changes with before/after values
3. **Validation Error Reporting** - Detailed error messages with row numbers and suggestions

## Schemas Implemented

### 1. Validation Error Schemas

#### `ValidationErrorDetail`
Represents a single validation error with detailed context:
- **field**: Field name where error occurred
- **row**: Row number in import file (if applicable)
- **sheet**: Excel sheet name (if applicable)
- **error_code**: Programmatic error code
- **message**: Human-readable error message
- **suggestion**: Fix suggestion
- **value**: The invalid value

#### `ValidationErrorSchema`
Comprehensive validation result:
- **is_valid**: Whether validation passed
- **errors**: List of validation errors
- **error_count**: Total error count (auto-calculated)
- **warning_count**: Total warning count (auto-calculated)
- **warnings**: List of non-blocking warnings

**Requirements Coverage**: 14.1-14.8 (Data validation and error handling)

### 2. Import Data Schemas

#### Entity-Specific Import Schemas
- `ImportUniversityData` - University import structure
- `ImportProgramData` - Study program import with university linking
- `ImportTrackData` - Academic track import
- `ImportSemesterData` - Semester import
- `ImportTeachingUnitData` - Teaching unit import
- `ImportCourseData` - Course import with prerequisites

#### `ImportDataSchema`
Main schema for Excel import validation:
- Validates complete curriculum import structure
- Supports all entity types in a single file
- Validates structural and semantic correctness
- Includes ECTS totals and prerequisite chain validation

**Requirements Coverage**: 9.1-9.10 (Bulk curriculum import system)

#### `ImportPreviewResponse`
Preview of entities to be created:
- Counts for each entity type
- Sample data for preview
- Auto-calculated total entities

**Requirements Coverage**: 9.4 (Display preview before import)

#### `ImportSummaryResponse`
Summary after import execution:
- Import ID and timestamp
- Success status
- Counts of created entities
- Auto-calculated total
- Error message if failed

**Requirements Coverage**: 9.10 (Display summary of created entities)

### 3. Audit Log Schemas

#### `FieldChange`
Represents a single field change:
- **field_name**: Technical field name
- **field_display_name**: Human-readable field name
- **old_value**: Value before change
- **new_value**: Value after change

#### `AuditLogResponse`
Complete audit log entry:
- **entity_type**: Type of modified entity
- **entity_id**: ID of modified entity
- **operation**: create, update, or delete
- **user_id, user_email, user_name**: User who made the change
- **timestamp**: When the change occurred
- **before_value**: Complete state before operation
- **after_value**: Complete state after operation
- **changes**: Detailed field-level changes for updates
- **description**: Human-readable description

**Requirements Coverage**: 
- 16.1: Log all operations with timestamp and user info
- 16.5: Display before/after values for updates

#### `AuditLogListResponse`
Paginated list of audit logs:
- List of audit log entries
- Pagination metadata (total, page, page_size, total_pages)

#### `AuditLogFilterParams`
Query parameters for filtering audit logs:
- Filter by entity type, entity ID, operation, user, date range
- Pagination support

#### `EntityHistoryResponse`
Change history for a specific entity:
- Entity identification
- Chronological list of changes
- Creation and last modification metadata

**Requirements Coverage**: 16.4 (View change history for individual entities)

## Enums

### `OperationType`
- `CREATE` - Entity creation
- `UPDATE` - Entity update
- `DELETE` - Entity deletion

### `EntityType`
Supported entity types for audit logging:
- UNIVERSITY, CAMPUS, STUDY_PROGRAM, ACADEMIC_TRACK
- SEMESTER, TEACHING_UNIT, COURSE, PREREQUISITE
- VALIDATION_RULE, USER, ROLE

## Features

### Auto-Calculation
Several schemas auto-calculate totals from list lengths:
- `ValidationErrorSchema` - error_count and warning_count
- `ImportPreviewResponse` - total_entities
- `ImportSummaryResponse` - total_entities_created

This is implemented using `model_post_init()` hooks.

### Comprehensive Examples
All schemas include JSON schema examples for:
- API documentation
- Frontend integration reference
- Testing

### Validation
- All imports validated for:
  - Field ranges (ECTS: 1-30, coefficient: 0.1-10.0, difficulty: 1-5)
  - Required fields
  - Structural correctness
  - Business rules (prerequisite chains, ECTS totals)

## Usage Example

```python
from app.schemas import (
    ValidationErrorSchema,
    ImportDataSchema,
    ImportPreviewResponse,
    ImportSummaryResponse,
    AuditLogResponse,
)

# Validation errors
validation_result = ValidationErrorSchema(
    is_valid=False,
    errors=[
        ValidationErrorDetail(
            field="ects_credits",
            row=15,
            message="ECTS must be between 1 and 30"
        )
    ]
)

# Import preview
preview = ImportPreviewResponse(
    universities_count=2,
    courses_count=50,
    # total_entities auto-calculated
)

# Audit log
audit_log = AuditLogResponse(
    entity_type="course",
    entity_id=123,
    operation=OperationType.UPDATE,
    user_email="admin@university.de",
    timestamp=datetime.now(),
    changes=[
        FieldChange(
            field_name="ects_credits",
            old_value=5,
            new_value=6
        )
    ]
)
```

## Integration

These schemas are exported in `app/schemas/__init__.py` and ready for use in:
- Import API endpoints (`/api/v1/admin/imports/*`)
- Audit API endpoints (`/api/v1/admin/audit/*`)
- Validation services
- Frontend integration

## Testing

All schemas have been validated with:
- Pydantic validation rules
- Auto-calculation features
- JSON serialization
- Example data matching
