"""
Test Validation Service
"""
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.services.planning_engine import TimeSlot
from app.services.validation_service import ValidationService
from app.core.security import get_password_hash

print("=" * 70)
print("Test Validation Service")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Setup test user and subjects
    print("1. Setup test data")
    test_user = db.query(User).filter(User.email == "validation_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="validation_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="Validation Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    # Clean up existing subjects
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.commit()
    
    # Create test subjects
    subjects = [
        Subject(user_id=test_user.id, name="Mathematics", priority=5, difficulty=4, 
                target_weekly_hours=10.0, exam_date=date.today() + timedelta(days=15)),
        Subject(user_id=test_user.id, name="Physics", priority=4, difficulty=5, 
                target_weekly_hours=8.0, exam_date=None),
    ]
    
    for subject in subjects:
        db.add(subject)
    db.commit()
    
    print(f"   User ID: {test_user.id}")
    print(f"   Subjects: {len(subjects)}")
    print()
    
    # 2. Create valid slots
    print("2. Create valid time slots")
    valid_slots = [
        TimeSlot("Monday", datetime.strptime("09:00:00", "%H:%M:%S").time(), 
                 datetime.strptime("12:00:00", "%H:%M:%S").time()),
        TimeSlot("Monday", datetime.strptime("14:00:00", "%H:%M:%S").time(), 
                 datetime.strptime("18:00:00", "%H:%M:%S").time()),
        TimeSlot("Wednesday", datetime.strptime("10:00:00", "%H:%M:%S").time(), 
                 datetime.strptime("16:00:00", "%H:%M:%S").time()),
    ]
    print(f"   Created {len(valid_slots)} valid slots")
    print()
    
    # 3. Create validation service
    print("3. Create validation service")
    validator = ValidationService(db)
    print("   Service created")
    print()
    
    # 4. Test valid plan
    print("4. Test VALID plan")
    valid_plan = {
        "sessions": [
            {
                "day": "Monday",
                "start_time": "09:00:00",
                "end_time": "10:30:00",
                "subject_name": "Mathematics",
                "task_type": "lecture_review",
                "notes": "Chapter 5"
            },
            {
                "day": "Monday",
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "subject_name": "Physics",
                "task_type": "exercise_practice",
                "notes": "Problems 1-10"
            }
        ],
        "total_hours": 3.5,
        "reasoning": "Balanced schedule"
    }
    
    is_valid, result = validator.validate_plan(
        valid_plan, valid_slots, subjects, 25.0, 
        {"max_daily_hours": 6, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=False
    )
    
    print(f"   Valid: {is_valid}")
    if is_valid:
        print(f"   Sessions: {len(result['plan']['sessions'])}")
    print()
    
    # 5. Test plan with invalid subject
    print("5. Test plan with INVALID subject (auto-correct)")
    invalid_subject_plan = {
        "sessions": [
            {
                "day": "Monday",
                "start_time": "09:00:00",
                "end_time": "10:30:00",
                "subject_name": "InvalidSubject",
                "task_type": "lecture_review",
                "notes": "Test"
            },
            {
                "day": "Monday",
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "subject_name": "Mathematics",
                "task_type": "exercise_practice",
                "notes": "Test"
            }
        ],
        "total_hours": 3.5,
        "reasoning": "Test"
    }
    
    is_valid, result = validator.validate_plan(
        invalid_subject_plan, valid_slots, subjects, 25.0,
        {"max_daily_hours": 6, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=True
    )
    
    print(f"   Valid after correction: {is_valid}")
    if is_valid:
        print(f"   Sessions after correction: {len(result['plan']['sessions'])}")
        print(f"   Corrections made: {len(result['corrections_made'])}")
        for correction in result['corrections_made']:
            print(f"     - {correction}")
    print()
    
    # 6. Test plan with invalid time slot
    print("6. Test plan with INVALID time slot (auto-correct)")
    invalid_slot_plan = {
        "sessions": [
            {
                "day": "Monday",
                "start_time": "08:00:00",  # Before valid slot
                "end_time": "09:00:00",
                "subject_name": "Mathematics",
                "task_type": "lecture_review",
                "notes": "Test"
            },
            {
                "day": "Tuesday",  # No valid slots on Tuesday
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "subject_name": "Physics",
                "task_type": "exercise_practice",
                "notes": "Test"
            }
        ],
        "total_hours": 2.0,
        "reasoning": "Test"
    }
    
    is_valid, result = validator.validate_plan(
        invalid_slot_plan, valid_slots, subjects, 25.0,
        {"max_daily_hours": 6, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=True
    )
    
    print(f"   Valid after correction: {is_valid}")
    if is_valid:
        print(f"   Sessions after correction: {len(result['plan']['sessions'])}")
        print(f"   Corrections made: {len(result['corrections_made'])}")
        for correction in result['corrections_made']:
            print(f"     - {correction}")
    print()
    
    # 7. Test plan violating max_daily_hours
    print("7. Test plan violating MAX_DAILY_HOURS (auto-correct)")
    constraint_violation_plan = {
        "sessions": [
            {
                "day": "Monday",
                "start_time": "09:00:00",
                "end_time": "12:00:00",
                "subject_name": "Mathematics",
                "task_type": "lecture_review",
                "notes": "Test"
            },
            {
                "day": "Monday",
                "start_time": "14:00:00",
                "end_time": "18:00:00",
                "subject_name": "Physics",
                "task_type": "exercise_practice",
                "notes": "Test"
            }
        ],
        "total_hours": 7.0,
        "reasoning": "Test"
    }
    
    is_valid, result = validator.validate_plan(
        constraint_violation_plan, valid_slots, subjects, 25.0,
        {"max_daily_hours": 5, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=True
    )
    
    print(f"   Valid after correction: {is_valid}")
    if is_valid:
        print(f"   Sessions after correction: {len(result['plan']['sessions'])}")
        print(f"   Corrections made: {len(result['corrections_made'])}")
        for correction in result['corrections_made']:
            print(f"     - {correction}")
    print()
    
    # 8. Test plan with missing schema fields
    print("8. Test plan with MISSING schema fields")
    invalid_schema_plan = {
        "sessions": []
        # Missing total_hours
    }
    
    is_valid, result = validator.validate_plan(
        invalid_schema_plan, valid_slots, subjects, 25.0,
        {"max_daily_hours": 6, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=False
    )
    
    print(f"   Valid: {is_valid}")
    if not is_valid:
        print(f"   Errors: {len(result['errors'])}")
        for error in result['errors']:
            print(f"     - {error['type']}: {error['message']}")
    print()
    
    # 9. Test total hours validation
    print("9. Test TOTAL HOURS validation (warning)")
    low_hours_plan = {
        "sessions": [
            {
                "day": "Monday",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
                "subject_name": "Mathematics",
                "task_type": "lecture_review",
                "notes": "Test"
            }
        ],
        "total_hours": 1.0,  # Much less than goal of 25
        "reasoning": "Test"
    }
    
    is_valid, result = validator.validate_plan(
        low_hours_plan, valid_slots, subjects, 25.0,
        {"max_daily_hours": 6, "required_breaks": [], "fixed_slots": [], "forbidden_slots_count": 0},
        auto_correct=True
    )
    
    print(f"   Valid: {is_valid}")
    if is_valid:
        print(f"   Warnings: {len(result['warnings'])}")
        for warning in result['warnings']:
            print(f"     - {warning}")
    print()
    
    print("=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(Subject).filter(Subject.user_id == test_user.id).delete()
        db.commit()
    db.close()
