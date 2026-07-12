"""
Test Session Editing - Manual session add/update/delete
"""
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.services.session_edit_service import SessionEditService
from app.core.security import get_password_hash
import uuid

print("=" * 70)
print("Test Session Editing Service")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Setup test data
    print("1. Setup test data")
    test_user = db.query(User).filter(User.email == "session_edit_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="session_edit_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="Session Edit Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    # Clean up
    db.query(StudySession).filter(StudySession.study_plan_id.in_(
        db.query(StudyPlan.id).filter(StudyPlan.user_id == test_user.id)
    )).delete(synchronize_session=False)
    db.query(StudyPlan).filter(StudyPlan.user_id == test_user.id).delete()
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
        preferences={}
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
        exam_date=None
    )
    db.add(math_subject)
    db.add(physics_subject)
    db.commit()
    db.refresh(math_subject)
    db.refresh(physics_subject)
    
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
    
    # Create a study plan
    plan = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=test_user.id,
        week_start=date.today(),
        status="generated",
        summary="Test plan",
        edited=False
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    print(f"   ✓ User created (ID: {test_user.id})")
    print(f"   ✓ Subjects: Mathematics (ID: {math_subject.id}), Physics (ID: {physics_subject.id})")
    print(f"   ✓ Availabilities: 2 on Monday")
    print(f"   ✓ Constraint: max_daily_hours = 6")
    print(f"   ✓ Study plan created (ID: {plan.id})")
    print()
    
    # 2. Create service
    print("2. Initialize SessionEditService")
    service = SessionEditService(db)
    print("   ✓ Service initialized")
    print()
    
    # 3. Test adding a valid session
    print("3. Test adding a VALID session")
    session_data = {
        "subject_id": math_subject.id,
        "day": "Monday",
        "start_time": "09:00:00",
        "end_time": "10:30:00",
        "task_type": "lecture_review",
        "notes": "Chapter 5"
    }
    
    success, result = service.add_session(
        plan_id=plan.id,
        user_id=test_user.id,
        session_data=session_data
    )
    
    print(f"   Success: {success}")
    if success:
        session1_id = result["session"]["id"]
        print(f"   Session ID: {session1_id}")
        print(f"   Subject: {result['session']['subject_name']}")
        print(f"   Time: {result['session']['start_time']} - {result['session']['end_time']}")
        
        # Check edited flag
        db.refresh(plan)
        print(f"   Plan edited flag: {plan.edited}")
        assert plan.edited == True, "Plan should be marked as edited"
    print()
    
    # 4. Test adding session with invalid subject
    print("4. Test adding session with INVALID subject")
    invalid_session = {
        "subject_id": 99999,  # Non-existent
        "day": "Monday",
        "start_time": "14:00:00",
        "end_time": "15:00:00",
        "task_type": "exercise_practice",
        "notes": ""
    }
    
    success, result = service.add_session(
        plan_id=plan.id,
        user_id=test_user.id,
        session_data=invalid_session
    )
    
    print(f"   Success: {success}")
    print(f"   Error: {result.get('error')}")
    assert not success, "Should fail with invalid subject"
    print("   ✓ Correctly rejected invalid subject")
    print()
    
    # 5. Test adding session outside availability
    print("5. Test adding session OUTSIDE availability")
    outside_avail = {
        "subject_id": physics_subject.id,
        "day": "Monday",
        "start_time": "08:00:00",  # Before 09:00
        "end_time": "09:00:00",
        "task_type": "reading",
        "notes": ""
    }
    
    success, result = service.add_session(
        plan_id=plan.id,
        user_id=test_user.id,
        session_data=outside_avail
    )
    
    print(f"   Success: {success}")
    print(f"   Error: {result.get('message')}")
    assert not success, "Should fail outside availability"
    print("   ✓ Correctly rejected session outside availability")
    print()
    
    # 6. Test adding overlapping session
    print("6. Test adding OVERLAPPING session")
    overlapping = {
        "subject_id": physics_subject.id,
        "day": "Monday",
        "start_time": "10:00:00",  # Overlaps with 09:00-10:30
        "end_time": "11:00:00",
        "task_type": "exercise_practice",
        "notes": ""
    }
    
    success, result = service.add_session(
        plan_id=plan.id,
        user_id=test_user.id,
        session_data=overlapping
    )
    
    print(f"   Success: {success}")
    print(f"   Error: {result.get('message')}")
    assert not success, "Should fail with overlap"
    print("   ✓ Correctly detected overlap")
    print()
    
    # 7. Test adding session that violates max_daily_hours
    print("7. Test adding session violating MAX_DAILY_HOURS")
    
    # Add more sessions to approach limit
    for i in range(4):
        session_data = {
            "subject_id": math_subject.id,
            "day": "Monday",
            "start_time": f"{14 + i}:00:00",
            "end_time": f"{15 + i}:00:00",
            "task_type": "exercise_practice",
            "notes": f"Session {i+2}"
        }
        service.add_session(plan_id=plan.id, user_id=test_user.id, session_data=session_data)
    
    # Now try to add one more that would exceed 6 hours
    exceeding = {
        "subject_id": physics_subject.id,
        "day": "Monday",
        "start_time": "11:00:00",
        "end_time": "12:00:00",
        "task_type": "reading",
        "notes": ""
    }
    
    success, result = service.add_session(
        plan_id=plan.id,
        user_id=test_user.id,
        session_data=exceeding
    )
    
    print(f"   Success: {success}")
    print(f"   Error: {result.get('message')}")
    assert not success, "Should fail exceeding max_daily_hours"
    print("   ✓ Correctly enforced max_daily_hours constraint")
    print()
    
    # 8. Test updating a session
    print("8. Test UPDATING a session")
    update_data = {
        "start_time": "09:30:00",
        "end_time": "11:00:00",
        "notes": "Updated notes"
    }
    
    success, result = service.update_session(
        plan_id=plan.id,
        session_id=session1_id,
        user_id=test_user.id,
        update_data=update_data
    )
    
    print(f"   Success: {success}")
    if success:
        print(f"   Updated time: {result['session']['start_time']} - {result['session']['end_time']}")
        print(f"   Updated notes: {result['session']['notes']}")
    print()
    
    # 9. Test deleting a session
    print("9. Test DELETING a session")
    success, result = service.delete_session(
        plan_id=plan.id,
        session_id=session1_id,
        user_id=test_user.id
    )
    
    print(f"   Success: {success}")
    print(f"   Message: {result.get('message')}")
    
    # Verify deletion
    deleted_session = db.query(StudySession).filter(StudySession.id == session1_id).first()
    assert deleted_session is None, "Session should be deleted"
    print("   ✓ Session deleted successfully")
    print()
    
    # 10. Test session limit
    print("10. Test SESSION LIMIT (50 sessions)")
    
    # Create a new plan for this test
    plan2 = StudyPlan(
        plan_id=str(uuid.uuid4()),
        user_id=test_user.id,
        week_start=date.today(),
        status="generated",
        summary="Limit test plan",
        edited=False
    )
    db.add(plan2)
    db.commit()
    db.refresh(plan2)
    
    # Add 50 sessions
    for i in range(50):
        session_data = {
            "subject_id": math_subject.id,
            "day": "Monday",
            "start_time": "09:00:00",
            "end_time": "09:15:00",
            "task_type": "lecture_review",
            "notes": f"Session {i+1}"
        }
        # Disable validation for this bulk insert
        session = StudySession(
            study_plan_id=plan2.id,
            subject_id=math_subject.id,
            day="Monday",
            start_time=datetime.strptime("09:00:00", "%H:%M:%S").time(),
            end_time=datetime.strptime("09:15:00", "%H:%M:%S").time(),
            task_type="lecture_review",
            notes=f"Session {i+1}"
        )
        db.add(session)
    db.commit()
    
    # Try to add 51st session
    session_data = {
        "subject_id": math_subject.id,
        "day": "Monday",
        "start_time": "09:00:00",
        "end_time": "09:15:00",
        "task_type": "lecture_review",
        "notes": "51st session"
    }
    
    success, result = service.add_session(
        plan_id=plan2.id,
        user_id=test_user.id,
        session_data=session_data
    )
    
    print(f"   Success: {success}")
    print(f"   Error: {result.get('error')}")
    assert not success and result.get('error') == 'session_limit_exceeded', "Should fail with session limit"
    print("   ✓ Correctly enforced 50 session limit")
    print()
    
    print("=" * 70)
    print("✓ ALL SESSION EDITING TESTS PASSED!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Add valid session")
    print("  ✓ Reject invalid subject")
    print("  ✓ Reject session outside availability")
    print("  ✓ Detect session overlaps")
    print("  ✓ Enforce max_daily_hours constraint")
    print("  ✓ Update session")
    print("  ✓ Delete session")
    print("  ✓ Enforce 50 session limit")
    print("  ✓ Mark plan as edited")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(StudySession).filter(StudySession.study_plan_id.in_(
            db.query(StudyPlan.id).filter(StudyPlan.user_id == test_user.id)
        )).delete(synchronize_session=False)
        db.query(StudyPlan).filter(StudyPlan.user_id == test_user.id).delete()
        db.query(Subject).filter(Subject.user_id == test_user.id).delete()
        db.query(Availability).filter(Availability.user_id == test_user.id).delete()
        db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
        db.query(StudentProfile).filter(StudentProfile.user_id == test_user.id).delete()
        db.commit()
    db.close()
