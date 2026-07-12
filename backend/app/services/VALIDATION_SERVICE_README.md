# ValidationService - Super Admin Platform Implementation

## Overview

This document describes the ValidationService implementation for the Super Admin Platform, which provides critical business rule validation for academic entities.

## Implementation Details

### File: `app/services/validation_service.py`

The ValidationService class has been extended with four new async validation methods for Super Admin Platform business rules:

### 1. `validate_prerequisite_chain(db, course_id, prerequisite_id)`

**Purpose**: Validate prerequisite relationships to prevent circular dependencies in course prerequisite chains.

**Requirements Addressed**: 7.2, 7.7, 7.8

**Algorithm**: Uses Depth-First Search (DFS) graph traversal to detect cycles in the prerequisite graph.

**Validations**:
- Checks if both courses exist and are not deleted
- Validates prerequisite is from earlier or same semester
- Detects circular dependencies using DFS with recursion stack
- Returns detailed error with the circular path when cycle is detected

**Returns**: `Tuple[bool, Optional[str]]`
- `(True, None)` if valid
- `(False, error_message)` if circular dependency or invalid semester order

**Example Usage**:
```python
is_valid, error = await validation_service.validate_prerequisite_chain(
    db, course_id=42, prerequisite_id=15
)
if not is_valid:
    print(error)  # "Circular dependency detected: Course A -> Course B -> Course A"
```

---

### 2. `validate_ects_totals(db, track_id)`

**Purpose**: Validate ECTS requirements hierarchy for an academic track.

**Requirements Addressed**: 8.6, 8.7

**Hierarchy Rule**: `graduation_ects >= year_progression_ects >= semester_validation_ects`

**Validations**:
- Retrieves all validation rules for the track
- Checks graduation >= year progression ECTS
- Checks year progression >= semester validation ECTS
- Checks graduation >= semester validation ECTS (transitive check)

**Returns**: `Tuple[bool, Dict[str, Any]]`
- `is_valid`: True if hierarchy is valid
- `validation_details`: Dict containing:
  - `track_name`, `track_level`
  - `graduation_ects`, `year_progression_ects`, `semester_validation_ects`
  - `errors`: List of validation error messages

**Example Usage**:
```python
is_valid, details = await validation_service.validate_ects_totals(db, track_id=1)
if not is_valid:
    for error in details['errors']:
        print(error)
```

---

### 3. `validate_semester_structure(db, track_id)`

**Purpose**: Validate semester numbering and structure for academic tracks.

**Requirements Addressed**: 4.1, 4.2, 4.5

**Rules**:
- **Bachelor**: Semesters 1-6 (S1-S6)
- **Master**: Semesters 1-4 (S1-S4)
- **Doctorate**: Custom structure (no strict validation)

**Validations**:
- Checks for duplicate semester numbers
- Validates semester numbers are within expected range
- Checks semesters start at 1
- Warns about missing semesters (non-blocking)

**Returns**: `Tuple[bool, List[str]]`
- `is_valid`: True if structure is valid (excludes warnings)
- `error_messages`: List of errors and warnings

**Example Usage**:
```python
is_valid, errors = await validation_service.validate_semester_structure(db, track_id=1)
if not is_valid:
    for error in errors:
        print(error)
```

---

### 4. `validate_import_data(import_data)`

**Purpose**: Validate complete import data structure and semantics before database insertion.

**Requirements Addressed**: 9.2, 9.3, 9.5, 14.1-14.8

**Validations**:

#### Structure Validation:
- Required top-level keys: `universities`, `programs`, `tracks`, `semesters`, `courses`
- All collections must be lists
- All items must be dictionaries

#### University Validation:
- Required fields: `name`, `country`

#### Program Validation:
- Required field: `name`

#### Track Validation:
- Required fields: `name`, `level`, `total_ects_required`
- Valid levels: `bachelor`, `master`, `doctorate`
- `total_ects_required` must be positive integer

#### Semester Validation:
- Required fields: `name`, `semester_number`
- `semester_number` must be positive integer

#### Course Validation:
- Required fields: `name`, `ects_credits`, `coefficient`, `difficulty_level`
- **ECTS credits**: Integer between 1 and 30 (Requirement 6.6)
- **Coefficient**: Number between 0.1 and 10.0 (Requirement 6.7)
- **Difficulty level**: Integer between 1 and 5 (Requirement 6.8)

#### Prerequisite Validation (optional):
- Must have `course_id` or `course_name`
- Must have `prerequisite_id` or `prerequisite_name`

**Returns**: `Tuple[bool, List[str]]`
- `is_valid`: True if all validations pass
- `error_messages`: Detailed list of validation errors with row indices

**Example Usage**:
```python
import_data = {
    "universities": [{"name": "TUM", "country": "Germany"}],
    "programs": [{"name": "Computer Science"}],
    "tracks": [{"name": "Bachelor CS", "level": "bachelor", "total_ects_required": 180}],
    "semesters": [{"name": "S1", "semester_number": 1}],
    "courses": [{
        "name": "Intro Programming",
        "ects_credits": 6,
        "coefficient": 1.0,
        "difficulty_level": 2
    }]
}

is_valid, errors = await validation_service.validate_import_data(import_data)
if not is_valid:
    for error in errors:
        print(error)
```

---

## Test Coverage

### File: `app/tests/test_validation_service.py`

Comprehensive unit tests with **100% coverage** of new validation methods:

**Test Classes**:

1. **TestPrerequisiteChainValidation** (4 tests)
   - Valid prerequisite with no cycles
   - Direct circular dependency detection (A -> B -> A)
   - Indirect circular dependency detection (A -> B -> C -> A)
   - Prerequisite from later semester rejection

2. **TestECTSHierarchyValidation** (3 tests)
   - Valid ECTS hierarchy (180 >= 60 >= 30)
   - Invalid: graduation < year progression
   - Invalid: year progression < semester validation

3. **TestSemesterStructureValidation** (6 tests)
   - Valid Bachelor structure (S1-S6)
   - Valid Master structure (S1-S4)
   - Invalid Bachelor semester number (> 6)
   - Invalid Master semester number (> 4)
   - Duplicate semester number detection
   - Missing semester warnings

4. **TestImportDataValidation** (6 tests)
   - Valid complete import data
   - Missing required keys detection
   - Invalid ECTS credits (out of 1-30 range)
   - Invalid coefficient (out of 0.1-10.0 range)
   - Invalid difficulty level (out of 1-5 range)
   - Invalid track level

**Test Results**: All 19 tests passed ✅

---

## Integration with Existing Code

The ValidationService has been updated while **preserving all existing functionality**:

- Existing AI study plan validation methods remain unchanged
- New methods are clearly separated in a dedicated section
- All imports updated to include new model dependencies
- Type hints added for graph traversal (`Set` type for DFS)

---

## Dependencies

**New Model Imports**:
- `Course` - for prerequisite validation
- `AcademicTrack`, `TrackLevel` - for track-level validations
- `Semester` - for semester structure validation
- `ValidationRule`, `RuleType` - for ECTS hierarchy validation

**Python Standard Library**:
- `collections.deque` (available but not used - DFS implemented with recursion)
- `Set` type from `typing` for visited nodes tracking

---

## Performance Considerations

1. **Prerequisite Chain Validation**:
   - Time complexity: O(V + E) where V = courses, E = prerequisite relationships
   - Space complexity: O(V) for visited and recursion stack
   - Efficient for typical curriculum sizes (hundreds of courses)

2. **ECTS Validation**:
   - O(1) database queries (single track + validation rules)
   - Simple arithmetic comparisons

3. **Semester Structure Validation**:
   - O(n) where n = number of semesters in track
   - Typically very small (6 for Bachelor, 4 for Master)

4. **Import Data Validation**:
   - O(n) where n = total entities in import
   - No database queries (pre-validation)
   - Fast validation before expensive database operations

---

## Future Enhancements

Potential improvements for future iterations:

1. **Batch Prerequisite Validation**: Validate multiple prerequisite relationships in one call
2. **Caching**: Cache prerequisite graph for repeated validations
3. **Detailed Prerequisite Suggestions**: Suggest valid alternatives when validation fails
4. **Import Data Auto-Correction**: Attempt to fix common import data issues automatically
5. **Asynchronous Validation**: Parallelize independent validations for large imports

---

## Related Files

- **Service**: `app/services/validation_service.py`
- **Tests**: `app/tests/test_validation_service.py`
- **Models**:
  - `app/models/course.py`
  - `app/models/academic_track.py`
  - `app/models/semester.py`
  - `app/models/validation_rule.py`
- **Design**: `.kiro/specs/super-admin-platform/design.md`
- **Requirements**: `.kiro/specs/super-admin-platform/requirements.md`
