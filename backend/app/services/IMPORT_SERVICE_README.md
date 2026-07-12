# Import Service

The Import Service provides bulk curriculum import capabilities for the Super Admin Platform, allowing administrators to import complete academic structures from Excel files.

## Features

- **Excel File Parsing**: Parse structured Excel files containing university curriculum data
- **Comprehensive Validation**: Both structural and semantic validation with detailed error reporting
- **Preview Generation**: Generate previews of entities to be created before import
- **Transactional Execution**: All imports execute as single database transactions with automatic rollback on errors
- **Audit Logging**: Integration with AuditService to track all import operations
- **Row-Level Error Reporting**: Validation errors include row numbers and specific messages

## Requirements Coverage

This service implements Requirements 9.1-9.10:

- 9.1: Excel file acceptance in predefined format
- 9.2: Structural validation
- 9.3: Semantic validation (ECTS totals, prerequisite chains)
- 9.4: Preview generation
- 9.5: Row-level error reporting
- 9.6: Prevention of import on validation errors
- 9.7: Single transaction execution
- 9.8: Rollback on failure
- 9.9: Support for all entity types
- 9.10: Import summary display

## Excel File Structure

The import expects an Excel file with the following sheets:

### 1. Universities
Columns: `name`, `name_de`, `country`, `description`, `description_de`

### 2. Campuses
Columns: `university_name`, `name`, `name_de`, `location`, `description`, `description_de`

### 3. Programs
Columns: `name`, `name_de`, `code`, `description`, `description_de`

### 4. University_Programs (Links)
Columns: `university_name`, `program_name`

### 5. Tracks
Columns: `program_name`, `name`, `name_de`, `level`, `total_ects_required`, `description`, `description_de`, `graduation_conditions`

Valid levels: `bachelor`, `master`, `doctorate`

### 6. Semesters
Columns: `track_name`, `name`, `name_de`, `semester_number`, `ects_required`, `description`, `description_de`

### 7. TeachingUnits
Columns: `semester_name`, `name`, `name_de`, `code`, `ects_required`, `description`, `description_de`

### 8. Courses
Columns: `semester_name`, `teaching_unit_name`, `name`, `name_de`, `code`, `ects_credits`, `coefficient`, `difficulty_level`, `description`, `description_de`

Constraints:
- `ects_credits`: Integer between 1 and 30
- `coefficient`: Float between 0.1 and 10.0
- `difficulty_level`: Integer between 1 and 5

### 9. Prerequisites
Columns: `course_name`, `prerequisite_name`

## Usage

```python
from app.services.import_service import ImportService
from app.core.database import get_db

# Initialize service
db = next(get_db())
import_service = ImportService(db)

# Parse Excel file
import_data = import_service.parse_excel_file("curriculum.xlsx")

# Validate import data
is_valid, errors = await import_service.validate_import_data(import_data)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"Row {error['row']} in {error['sheet']}: {error['message']}")
else:
    # Generate preview
    preview = await import_service.preview_import(import_data)
    print(f"Will create {preview['total_entities']} entities")
    
    # Execute import
    result = await import_service.execute_import(import_data, user_id=1)
    print(f"Import successful: {result['created_counts']}")
```

## Validation Rules

### Structural Validation
- Required fields are present
- Data types are correct (int, float, str)
- ECTS, coefficient, and difficulty values are within valid ranges
- Track level is one of: bachelor, master, doctorate

### Semantic Validation
- All referenced entities exist (e.g., semester references valid track)
- No circular dependencies in prerequisite chains
- ECTS totals are consistent (with 20% tolerance)

### Business Rule Validation
- Prerequisite courses are from earlier or same semester
- University names are unique
- Program codes are unique (if provided)
- Course codes are unique (if provided)

## Error Handling

The service provides detailed error reporting:

```python
{
    "row": 5,
    "sheet": "Courses",
    "message": "ECTS credits must be an integer between 1 and 30",
    "type": "validation"
}
```

Error types:
- `validation`: Structural or constraint validation failure
- `circular_dependency`: Circular prerequisite dependency detected
- `ects_mismatch`: ECTS totals don't match requirements

## Transaction Management

All imports execute as a single database transaction:

1. Parse Excel file
2. Validate all data
3. Begin transaction
4. Create all entities
5. Log audit entries
6. Commit transaction

If any step fails, the entire transaction is rolled back, ensuring data consistency.

## Integration

The ImportService integrates with:

- **ValidationService**: For prerequisite chain validation and business rules
- **AuditService**: For logging all entity creations
- **Database Models**: All academic entity models (University, Program, Track, etc.)

## Testing

Comprehensive unit tests cover:
- Excel parsing
- Validation (structural, semantic, business rules)
- Preview generation
- Transactional execution
- Rollback on errors
- Audit logging

Run tests:
```bash
pytest app/services/test_import_service.py -v
```

## Dependencies

- `openpyxl`: Excel file parsing
- `SQLAlchemy`: Database ORM and transaction management
- `ValidationService`: Business rule validation
- `AuditService`: Change tracking
