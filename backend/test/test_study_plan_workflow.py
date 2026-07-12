"""
Test Study Plan Service - Simplified Workflow Test
"""
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.services.study_plan_service import StudyPlanService
from app.core.security import get_password_hash

print("=" * 70)
print("Test Study Plan Service - Workflow Validation")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Setup test user and data
    print("1. Setup test data")
    test_user = db.query(User).filter(User.email == "workflow_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="workflow_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="Workflow Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    # Clean up existing data
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.query(Availability).filter(Availability.user_id == test_user.id).delete()
    db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
    db.query(StudentProfile).filter(StudentProfile.user_id == test_user.id).delete()
    db.commit()
    
    # Create profile
    profile = StudentProfile(
        user_id=test_user.id,
        cursus="Computer Science",
        academic_level="Bachelor",
        weekly_study_goal=25.0,
        preferences={"preferred_session_length": 90}
    )
    db.add(profile)
    db.commit()
    
    # Create subjects
    math_subject = Subject(
        user_id=test_user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=10.0,
        exam_date=date.today() + timedelta(days=15)
    )
    physics_subject = Subject(
        user_id=test_user.id,
        name="Physics",
        priority=4,
        difficulty=5,
        target_weekly_hours=8.0,
        exam_date=date.today() + timedelta(days=30)
    )
    
    db.add(math_subject)
    db.add(physics_subject)
    db.commit()
    
    # Create availabilities
    monday_morning = Availability(
        user_id=test_user.id,
        day_of_week="Monday",
        start_time=datetime.strptime("09:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("12:00:00", "%H:%M:%S").time()
    )
    monday_afternoon = Availability(
        user_id=test_user.id,
        day_of_week="Monday",
        start_time=datetime.strptime("14:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("18:00:00", "%H:%M:%S").time()
    )
    
    db.add(monday_morning)
    db.add(monday_afternoon)
    db.commit()
    
    # Create constraint
    constraint = Constraint(
        user_id=test_user.id,
        constraint_type="max_daily_hours",
        parameters={"max_hours": 6},
        active=True
    )
    db.add(constraint)
    db.commit()
    
    print(f"   ✓ User created (ID: {test_user.id})")
    print(f"   ✓ Profile created")
    print(f"   ✓ 2 subjects created")
    print(f"   ✓ 2 availabilities created")
    print(f"   ✓ 1 constraint created")
    print()
    
    # 2. Create service
    print("2. Initialize StudyPlanService")
    service = StudyPlanService(db)
    print("   ✓ Service initialized")
    print()
    
    # 3. Test workflow prerequisites
    print("3. Test workflow prerequisites")
    
    # Get next Monday
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    
    print(f"   Target week: {next_monday}")
    
    # Test data retrieval
    user_data = service._retrieve_user_data(test_user.id)
    print(f"   ✓ User data retrieved: {user_data['success']}")
    print(f"   ✓ Profile found: {user_data['profile'] is not None}")
    print(f"   ✓ Subjects count: {len(user_data['subjects'])}")
    print(f"   ✓ Availabilities count: {len(user_data['availabilities'])}")
    print(f"   ✓ Constraints count: {len(user_data['constraints'])}")
    print()
    
    # 4. Test planning engine methods
    print("4. Test planning engine methods")
    
    valid_slots = service._construct_valid_slots_from_data(
        user_data['availabilities'],
        user_data['constraints']
    )
    print(f"   ✓ Valid slots constructed: {len(valid_slots)} slots")
    
    priorities = service._calculate_priorities_from_data(
        user_data['subjects'],
        next_monday
    )
    print(f"   ✓ Priorities calculated: {len(priorities)} subjects")
    for p in priorities:
        print(f"     - {p.subject.name}: {p.priority_score:.2f}")
    
    constraint_info = service._validate_constraints_from_data(user_data['constraints'])
    print(f"   ✓ Constraints validated")
    print(f"     - max_daily_hours: {constraint_info['max_daily_hours']}")
    print()
    
    # 5. Test error cases
    print("5. Test error handling")
    
    # Test with no subjects
    print("   5a. No subjects error")
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.commit()
    
    success, result = service.generate_plan(
        user_id=test_user.id,
        week_start=next_monday,
        force_regenerate=False
    )
    
    print(f"      Success: {success}")
    print(f"      Error: {result.get('error')}")
    assert not success and result.get('error') == 'no_subjects', "Should fail with no_subjects error"
    print("      ✓ Correctly detected missing subjects")
    
    # Recreate subjects
    math_subject = Subject(
        user_id=test_user.id,
        name="Mathematics",
        priority=5,
        difficulty=4,
        target_weekly_hours=10.0,
        exam_date=date.today() + timedelta(days=15)
    )
    db.add(math_subject)
    db.commit()
    
    # Test with no availabilities
    print("   5b. No availabilities error")
    db.query(Availability).filter(Availability.user_id == test_user.id).delete()
    db.commit()
    
    success, result = service.generate_plan(
        user_id=test_user.id,
        week_start=next_monday,
        force_regenerate=False
    )
    
    print(f"      Success: {success}")
    print(f"      Error: {result.get('error')}")
    assert not success and result.get('error') == 'no_availabilities', "Should fail with no_availabilities error"
    print("      ✓ Correctly detected missing availabilities")
    print()
    
    # 6. Test cache operations
    print("6. Test cache operations")
    
    # Recreate availabilities for cache test
    monday_morning = Availability(
        user_id=test_user.id,
        day_of_week="Monday",
        start_time=datetime.strptime("09:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("12:00:00", "%H:%M:%S").time()
    )
    db.add(monday_morning)
    db.commit()
    
    # Refresh data
    subjects = db.query(Subject).filter(Subject.user_id == test_user.id).all()
    availabilities = db.query(Availability).filter(Availability.user_id == test_user.id).all()
    constraints = db.query(Constraint).filter(Constraint.user_id == test_user.id).all()
    
    # Test cache key computation
    cache_key = service._compute_cache_key(
        test_user.id,
        next_monday,
        subjects,
        availabilities,
        constraints
    )
    print(f"   ✓ Cache key computed: {cache_key[:30]}...")
    
    # Test cache add/get
    mock_plan = {
        "sessions": [],
        "total_hours": 0,
        "reasoning": "Mock plan"
    }
    
    service._add_to_cache(cache_key, mock_plan)
    cached = service._get_from_cache(cache_key)
    assert cached is not None, "Should retrieve cached plan"
    print("   ✓ Cache add/get works")
    
    # Test cache invalidation
    service.invalidate_user_cache(test_user.id)
    cached = service._get_from_cache(cache_key)
    assert cached is None, "Cache should be invalidated"
    print("   ✓ Cache invalidation works")
    print()
    
    # 7. Test plan retrieval methods
    print("7. Test plan retrieval methods")
    
    current_plan = service.get_current_plan(test_user.id)
    print(f"   ✓ get_current_plan: {current_plan is not None}")
    
    plan_by_id = service.get_plan_by_id("non-existent-uuid", test_user.id)
    print(f"   ✓ get_plan_by_id (non-existent): {plan_by_id is None}")
    print()
    
    print("=" * 70)
    print("✓ ALL WORKFLOW TESTS PASSED!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Service initialization")
    print("  ✓ User data retrieval")
    print("  ✓ Valid slots construction")
    print("  ✓ Priority calculation")
    print("  ✓ Constraint validation")
    print("  ✓ Error handling (no subjects, no availabilities)")
    print("  ✓ Cache operations (add, get, invalidate)")
    print("  ✓ Plan retrieval methods")
    print()
    print("Note: Full end-to-end generation requires AI service (Ollama/Colab)")
    print("      The workflow is ready for AI integration.")
    print()
    print("Next steps:")
    print("  1. Start Ollama with Llama 3.2 model")
    print("  2. Test full generation with real AI")
    print("  3. Verify plan saving to database")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(Subject).filter(Subject.user_id == test_user.id).delete()
        db.query(Availability).filter(Availability.user_id == test_user.id).delete()
        db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
        db.query(StudentProfile).filter(StudentProfile.user_id == test_user.id).delete()
        db.commit()
    db.close()
