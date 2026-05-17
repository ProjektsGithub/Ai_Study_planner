"""
Database seeding script for development data
"""
import sys
from pathlib import Path
from datetime import datetime, date, time, timedelta, timezone
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import (
    User,
    StudentProfile,
    Subject,
    Availability,
    Constraint,
    StudyPlan,
    StudySession,
)
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_database():
    """Seed database with development data"""
    db: Session = SessionLocal()
    
    try:
        print("Seeding database with development data...")
        
        # Check if data already exists
        existing_user = db.query(User).filter(User.email == "student@example.com").first()
        if existing_user:
            print("✓ Database already seeded!")
            return
        
        # Create test user
        print("Creating test user...")
        user = User(
            email="student@example.com",
            password_hash=pwd_context.hash("password123"),
            name="Test Student",
            created_at=datetime.now(timezone.utc),
            is_active=True,
            failed_login_attempts=0,
        )
        db.add(user)
        db.flush()
        
        # Create student profile
        print("Creating student profile...")
        profile = StudentProfile(
            user_id=user.id,
            cursus="Computer Science",
            academic_level="Bachelor Year 3",
            weekly_study_goal=25.0,
            preferences={"preferred_study_time": "evening", "break_duration": 15},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(profile)
        
        # Create subjects
        print("Creating subjects...")
        subjects_data = [
            {"name": "Algorithms", "priority": 5, "difficulty": 4, "target_weekly_hours": 6.0, "exam_date": date.today() + timedelta(days=14)},
            {"name": "Database Systems", "priority": 4, "difficulty": 3, "target_weekly_hours": 5.0, "exam_date": date.today() + timedelta(days=21)},
            {"name": "Web Development", "priority": 3, "difficulty": 2, "target_weekly_hours": 4.0, "exam_date": date.today() + timedelta(days=28)},
            {"name": "Operating Systems", "priority": 4, "difficulty": 5, "target_weekly_hours": 5.0, "exam_date": date.today() + timedelta(days=35)},
            {"name": "Software Engineering", "priority": 3, "difficulty": 3, "target_weekly_hours": 5.0, "exam_date": None},
        ]
        
        subjects = []
        for subject_data in subjects_data:
            subject = Subject(
                user_id=user.id,
                created_at=datetime.now(timezone.utc),
                **subject_data
            )
            db.add(subject)
            subjects.append(subject)
        
        db.flush()
        
        # Create availabilities
        print("Creating availabilities...")
        availabilities_data = [
            # Weekdays
            {"day_of_week": "Monday", "start_time": time(18, 0), "end_time": time(22, 0)},
            {"day_of_week": "Tuesday", "start_time": time(18, 0), "end_time": time(22, 0)},
            {"day_of_week": "Wednesday", "start_time": time(18, 0), "end_time": time(22, 0)},
            {"day_of_week": "Thursday", "start_time": time(18, 0), "end_time": time(22, 0)},
            {"day_of_week": "Friday", "start_time": time(18, 0), "end_time": time(21, 0)},
            # Weekend
            {"day_of_week": "Saturday", "start_time": time(9, 0), "end_time": time(12, 0)},
            {"day_of_week": "Saturday", "start_time": time(14, 0), "end_time": time(18, 0)},
            {"day_of_week": "Sunday", "start_time": time(10, 0), "end_time": time(13, 0)},
            {"day_of_week": "Sunday", "start_time": time(15, 0), "end_time": time(19, 0)},
        ]
        
        for availability_data in availabilities_data:
            availability = Availability(
                user_id=user.id,
                created_at=datetime.now(timezone.utc),
                **availability_data
            )
            db.add(availability)
        
        # Create constraints
        print("Creating constraints...")
        constraints_data = [
            {
                "constraint_type": "max_daily_hours",
                "parameters": {"max_hours": 4.0},
                "active": True,
            },
            {
                "constraint_type": "required_break",
                "parameters": {"break_duration_minutes": 15, "break_after_minutes": 90},
                "active": True,
            },
            {
                "constraint_type": "forbidden_slot",
                "parameters": {"day": "Friday", "start_time": "21:00", "end_time": "23:59"},
                "active": True,
            },
        ]
        
        for constraint_data in constraints_data:
            constraint = Constraint(
                user_id=user.id,
                created_at=datetime.now(timezone.utc),
                **constraint_data
            )
            db.add(constraint)
        
        # Create a sample study plan
        print("Creating sample study plan...")
        plan = StudyPlan(
            plan_id=str(uuid.uuid4()),
            user_id=user.id,
            week_start=date.today() - timedelta(days=date.today().weekday()),  # Start of current week
            status="generated",
            summary="Balanced study plan focusing on upcoming exams",
            edited=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(plan)
        db.flush()
        
        # Create sample study sessions
        print("Creating sample study sessions...")
        sessions_data = [
            {"day": "Monday", "start_time": time(18, 0), "end_time": time(20, 0), "subject_id": subjects[0].id, "task_type": "revision", "notes": "Focus on sorting algorithms"},
            {"day": "Monday", "start_time": time(20, 15), "end_time": time(22, 0), "subject_id": subjects[1].id, "task_type": "exercises", "notes": "SQL practice"},
            {"day": "Tuesday", "start_time": time(18, 0), "end_time": time(20, 0), "subject_id": subjects[2].id, "task_type": "project", "notes": "Work on React components"},
            {"day": "Wednesday", "start_time": time(18, 0), "end_time": time(20, 30), "subject_id": subjects[0].id, "task_type": "exam_prep", "notes": "Past exam papers"},
            {"day": "Thursday", "start_time": time(18, 0), "end_time": time(20, 0), "subject_id": subjects[3].id, "task_type": "reading", "notes": "Chapter 5-6"},
            {"day": "Saturday", "start_time": time(9, 0), "end_time": time(12, 0), "subject_id": subjects[0].id, "task_type": "revision", "notes": "Graph algorithms"},
            {"day": "Sunday", "start_time": time(10, 0), "end_time": time(13, 0), "subject_id": subjects[4].id, "task_type": "exercises", "notes": "Design patterns"},
        ]
        
        for session_data in sessions_data:
            session = StudySession(
                study_plan_id=plan.id,
                **session_data
            )
            db.add(session)
        
        # Commit all changes
        db.commit()
        
        print("\n✓ Database seeded successfully!")
        print(f"\nTest credentials:")
        print(f"  Email: student@example.com")
        print(f"  Password: password123")
        print(f"\nCreated:")
        print(f"  - 1 user")
        print(f"  - 1 student profile")
        print(f"  - {len(subjects_data)} subjects")
        print(f"  - {len(availabilities_data)} availabilities")
        print(f"  - {len(constraints_data)} constraints")
        print(f"  - 1 study plan with {len(sessions_data)} sessions")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
