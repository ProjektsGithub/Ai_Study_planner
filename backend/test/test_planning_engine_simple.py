"""
Test simplifie du Planning Engine (sans caracteres Unicode)
"""
import sys
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.services.planning_engine import PlanningEngine
from app.core.security import get_password_hash
import json

print("=" * 70)
print("Test Planning Engine")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Create or get test user
    print("1. Setup test user")
    test_user = db.query(User).filter(User.email == "planning_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="planning_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="Planning Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    print(f"   User ID: {test_user.id}")
    
    # Clean up existing data
    db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
    db.query(Availability).filter(Availability.user_id == test_user.id).delete()
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.commit()
    print("   Data cleaned")
    print()
    
    # 2. Create subjects
    print("2. Create subjects")
    from datetime import datetime
    
    subjects = [
        Subject(user_id=test_user.id, name="Mathematics", priority=5, difficulty=4, 
                target_weekly_hours=10.0, exam_date=date.today() + timedelta(days=15)),
        Subject(user_id=test_user.id, name="Physics", priority=4, difficulty=5, 
                target_weekly_hours=8.0, exam_date=date.today() + timedelta(days=45)),
        Subject(user_id=test_user.id, name="Computer Science", priority=3, difficulty=3, 
                target_weekly_hours=12.0, exam_date=None),
    ]
    
    for subject in subjects:
        db.add(subject)
    db.commit()
    print(f"   Created {len(subjects)} subjects")
    print()
    
    # 3. Create availabilities
    print("3. Create availabilities")
    availabilities = [
        Availability(user_id=test_user.id, day_of_week="Monday", 
                    start_time=datetime.strptime("09:00:00", "%H:%M:%S").time(),
                    end_time=datetime.strptime("12:00:00", "%H:%M:%S").time()),
        Availability(user_id=test_user.id, day_of_week="Monday", 
                    start_time=datetime.strptime("14:00:00", "%H:%M:%S").time(),
                    end_time=datetime.strptime("18:00:00", "%H:%M:%S").time()),
        Availability(user_id=test_user.id, day_of_week="Wednesday", 
                    start_time=datetime.strptime("10:00:00", "%H:%M:%S").time(),
                    end_time=datetime.strptime("16:00:00", "%H:%M:%S").time()),
        Availability(user_id=test_user.id, day_of_week="Friday", 
                    start_time=datetime.strptime("08:00:00", "%H:%M:%S").time(),
                    end_time=datetime.strptime("12:00:00", "%H:%M:%S").time()),
    ]
    
    for avail in availabilities:
        db.add(avail)
    db.commit()
    print(f"   Created {len(availabilities)} availabilities")
    print()
    
    # 4. Create constraints
    print("4. Create constraints")
    constraints = [
        Constraint(user_id=test_user.id, constraint_type="forbidden_slot",
                  parameters={"day_of_week": "Monday", "start_time": "12:00:00", "end_time": "14:00:00"},
                  active=True),
        Constraint(user_id=test_user.id, constraint_type="max_daily_hours",
                  parameters={"max_hours": 6}, active=True),
        Constraint(user_id=test_user.id, constraint_type="required_break",
                  parameters={"duration_minutes": 15, "after_minutes": 90}, active=True),
    ]
    
    for constraint in constraints:
        db.add(constraint)
    db.commit()
    print(f"   Created {len(constraints)} constraints")
    print()
    
    # 5. Test Planning Engine - Full generation
    print("5. Generate planning data")
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    
    print(f"   SUCCESS - Data generated")
    print(f"   - Total subjects: {planning_data['total_subjects']}")
    print(f"   - Total slots: {planning_data['total_slots']}")
    print(f"   - Total slot hours: {planning_data['total_slot_hours']:.1f}h")
    print()
    
    # 6. Verify valid slots
    print("6. Verify valid slots")
    valid_slots = planning_data['valid_slots']
    print(f"   Found {len(valid_slots)} valid slots")
    for slot in valid_slots[:3]:
        print(f"   - {slot['day']}: {slot['start_time']}-{slot['end_time']} ({slot['duration_minutes']} min)")
    print()
    
    # 7. Verify subject priorities
    print("7. Verify subject priorities")
    priorities = planning_data['subject_priorities']
    print(f"   Calculated {len(priorities)} priorities")
    for priority in priorities:
        print(f"   - {priority['subject_name']}: {priority['priority_score']:.2f}")
    print()
    
    # 8. Verify constraints
    print("8. Verify constraints")
    constraint_info = planning_data['constraints']
    print(f"   - Max daily hours: {constraint_info['max_daily_hours']}")
    print(f"   - Required breaks: {len(constraint_info['required_breaks'])}")
    print(f"   - Forbidden slots: {constraint_info['forbidden_slots_count']}")
    print()
    
    # 9. Test forbidden slot removal
    print("9. Test forbidden slot removal")
    monday_slots = [s for s in planning_data['valid_slots'] if s['day'] == 'Monday']
    print(f"   Monday slots after forbidden removal: {len(monday_slots)}")
    for slot in monday_slots:
        print(f"   - {slot['start_time']}-{slot['end_time']}")
    print()
    
    # 10. Performance test
    print("10. Performance test")
    import time
    
    start_time = time.time()
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    end_time = time.time()
    
    duration = (end_time - start_time) * 1000
    print(f"   Generation completed in {duration:.2f}ms")
    
    if duration < 2000:
        print(f"   Performance OK (< 2 seconds)")
    else:
        print(f"   Performance SLOW (> 2 seconds)")
    print()
    
    print("=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
        db.query(Availability).filter(Availability.user_id == test_user.id).delete()
        db.query(Subject).filter(Subject.user_id == test_user.id).delete()
        db.commit()
    db.close()
