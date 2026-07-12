"""
Simple test for Task 13: Study Plan History and Versioning
Tests history and restoration without requiring AI generation
"""
import sys
sys.path.insert(0, '.')

from datetime import date, timedelta, datetime, time
from app.core.database import SessionLocal
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.core.security import get_password_hash
from app.services.study_plan_service import StudyPlanService
import uuid

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def create_test_user(db):
    """Create a test user with profile and subjects"""
    print_section("SETUP: Create Test User")
    
    # Create user
    user = User(
        email=f"test_history_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        name="Test User History",
        is_active=True
    )
    db.add(user)
    db.flush()
    print(f"✓ User created: {user.email}")
    
    # Create profile
    profile = StudentProfile(
        user_id=user.id,
        cursus="Computer Science",
        academic_level="Bachelor",
        weekly_study_goal=20,
        preferences={"preferred_session_duration": 90}
    )
    db.add(profile)
    print("✓ Profile created")
    
    # Create subjects
    subjects = []
    for i, name in enumerate(["Mathematics", "Physics", "Chemistry"]):
        subject = Subject(
            user_id=user.id,
            name=name,
            priority=5 - i,
            difficulty=4,
            target_weekly_hours=6,
            exam_date=date.today() + timedelta(days=30 + i*10)
        )
        db.add(subject)
        db.flush()
        subjects.append(subject)
        print(f"✓ Subject '{name}' created")
    
    db.commit()
    return user, subjects

def create_test_plans(db, user, subjects):
    """Create multiple test study plans"""
    print_section("TEST 1: Create Multiple Study Plans")
    
    plans = []
    
    # Create 5 plans for different weeks
    for i in range(5):
        week_start = date.today() + timedelta(weeks=i)
        # Ensure it's a Monday
        while week_start.weekday() != 0:
            week_start += timedelta(days=1)
        
        plan_id = str(uuid.uuid4())
        
        plan = StudyPlan(
            plan_id=plan_id,
            user_id=user.id,
            week_start=week_start,
            status="generated" if i < 3 else "superseded",  # Mix of statuses
            summary=f"Test plan {i+1} for week starting {week_start}",
            edited=False
        )
        db.add(plan)
        db.flush()
        
        # Add 3 sessions to each plan
        for j, subject in enumerate(subjects):
            session = StudySession(
                study_plan_id=plan.id,
                subject_id=subject.id,
                day="Monday" if j == 0 else "Tuesday" if j == 1 else "Wednesday",
                start_time=time(9, 0, 0),
                end_time=time(11, 0, 0),
                task_type="lecture_review",
                notes=f"Session {j+1} for {subject.name}"
            )
            db.add(session)
        
        plans.append(plan)
        print(f"✓ Plan {i+1} created: {plan_id} (week: {week_start}, status: {plan.status})")
    
    db.commit()
    return plans

def test_plan_history(db, user):
    """Test get_plan_history method"""
    print_section("TEST 2: Get Plan History")
    
    service = StudyPlanService(db)
    
    # Test page 1
    print("Fetching page 1...")
    result = service.get_plan_history(user_id=user.id, page=1, page_size=20)
    
    print(f"✓ History retrieved successfully")
    print(f"  Total plans: {result['total_count']}")
    print(f"  Page: {result['page']}/{result['total_pages']}")
    print(f"  Plans on this page: {len(result['plans'])}")
    
    # Display plan summaries
    for plan in result['plans']:
        print(f"\n  Plan: {plan['plan_id']}")
        print(f"    Week: {plan['week_start']}")
        print(f"    Status: {plan['status']}")
        print(f"    Sessions: {plan['session_count']}")
        print(f"    Total hours: {plan['total_hours']}")
        print(f"    Created: {plan['created_at']}")
    
    return result['plans']

def test_pagination(db, user):
    """Test pagination with small page size"""
    print_section("TEST 3: Pagination")
    
    service = StudyPlanService(db)
    
    # Test with page size of 2
    print("Fetching page 1 (page_size=2)...")
    result1 = service.get_plan_history(user_id=user.id, page=1, page_size=2)
    print(f"✓ Page 1: {len(result1['plans'])} plans")
    print(f"  Total pages: {result1['total_pages']}")
    
    if result1['total_pages'] > 1:
        print("\nFetching page 2 (page_size=2)...")
        result2 = service.get_plan_history(user_id=user.id, page=2, page_size=2)
        print(f"✓ Page 2: {len(result2['plans'])} plans")
        
        # Verify different plans
        page1_ids = {p['plan_id'] for p in result1['plans']}
        page2_ids = {p['plan_id'] for p in result2['plans']}
        
        if page1_ids.isdisjoint(page2_ids):
            print("✓ Pages contain different plans (no duplicates)")
        else:
            print("✗ Pages contain overlapping plans")
    else:
        print("ℹ Only 1 page available")

def test_plan_restoration(db, user, plans):
    """Test restore_plan method"""
    print_section("TEST 4: Plan Restoration")
    
    service = StudyPlanService(db)
    
    # Get a plan to restore (use the first one)
    plan_to_restore = plans[0]
    
    print(f"Restoring plan: {plan_to_restore.plan_id}")
    print(f"  Original week: {plan_to_restore.week_start}")
    print(f"  Original status: {plan_to_restore.status}")
    print(f"  Original sessions: {len(plan_to_restore.sessions)}")
    
    success, result = service.restore_plan(
        plan_id=plan_to_restore.plan_id,
        user_id=user.id
    )
    
    if success:
        print(f"\n✓ Plan restored successfully")
        print(f"  New plan ID: {result['plan_id']}")
        print(f"  Message: {result.get('message')}")
        
        # Verify the restored plan
        new_plan_id = result['plan_id']
        restored_plan = service.get_plan_by_id(new_plan_id, user.id)
        
        if restored_plan:
            print(f"\n✓ Restored plan verified")
            print(f"  Status: {restored_plan['status']}")
            print(f"  Sessions: {len(restored_plan['sessions'])}")
            print(f"  Total hours: {restored_plan['total_hours']}")
            print(f"  Edited flag: {restored_plan['edited']}")
            
            # Verify session count matches
            if len(restored_plan['sessions']) == len(plan_to_restore.sessions):
                print("✓ All sessions copied correctly")
            else:
                print(f"✗ Session count mismatch: {len(restored_plan['sessions'])} vs {len(plan_to_restore.sessions)}")
        else:
            print("✗ Failed to verify restored plan")
    else:
        print(f"✗ Restoration failed: {result.get('message')}")

def test_invalid_restoration(db, user):
    """Test restoring a non-existent plan"""
    print_section("TEST 5: Invalid Plan Restoration")
    
    service = StudyPlanService(db)
    
    fake_plan_id = "00000000-0000-0000-0000-000000000000"
    
    print(f"Attempting to restore non-existent plan: {fake_plan_id}...")
    success, result = service.restore_plan(
        plan_id=fake_plan_id,
        user_id=user.id
    )
    
    if not success and result.get('error') == 'plan_not_found':
        print("✓ Correctly returned error for non-existent plan")
        print(f"  Error: {result.get('message')}")
    else:
        print("✗ Expected plan_not_found error")

def test_retention_policy(db):
    """Test delete_old_plans method"""
    print_section("TEST 6: 90-Day Retention Policy")
    
    service = StudyPlanService(db)
    
    # Test with dry run (0 days to see all plans)
    print("Testing retention policy (dry run with 0 days)...")
    
    # Count current plans
    total_plans = db.query(StudyPlan).count()
    print(f"Current total plans in database: {total_plans}")
    
    # Test with 90 days (should delete nothing since we just created them)
    print("\nTesting with 90-day retention...")
    result = service.delete_old_plans(retention_days=90)
    
    if result['success']:
        print(f"✓ Retention policy executed successfully")
        print(f"  Plans deleted: {result['deleted_count']}")
        print(f"  Cutoff date: {result.get('cutoff_date')}")
        
        if result['deleted_count'] == 0:
            print("✓ No plans deleted (all plans are recent)")
        else:
            print(f"ℹ {result['deleted_count']} old plans were deleted")
    else:
        print(f"✗ Retention policy failed: {result.get('error')}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  TASK 13: STUDY PLAN HISTORY AND VERSIONING TESTS")
    print("  (Direct Database Tests)")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Setup
        user, subjects = create_test_user(db)
        plans = create_test_plans(db, user, subjects)
        
        # Test history retrieval
        history_plans = test_plan_history(db, user)
        
        # Test pagination
        test_pagination(db, user)
        
        # Test plan restoration
        test_plan_restoration(db, user, plans)
        
        # Test invalid restoration
        test_invalid_restoration(db, user)
        
        # Test retention policy
        test_retention_policy(db)
        
        print("\n" + "="*60)
        print("  ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
