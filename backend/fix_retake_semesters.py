"""
Script to fix retake_semesters data based on German Wiederholung rules

This script will:
1. For each student profile with retake_semesters
2. Validate that retake semesters follow the rules:
   - S4: can only retake S2
   - S5: can only retake S1 or S3
   - S6: can only retake S2 or S4
   - S7+: can retake any previous semester
3. Remove invalid retake semesters that don't follow the rules
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.student_profile import StudentProfile
from app.models.semester import Semester
from app.models.course import Course
from app.models.subject import Subject
from app.models.student_course_enrollment import StudentCourseEnrollment
from app.core.config import settings

# German Wiederholung rules: which semesters can be retaken per current semester
RETAKE_RULES = {
    1: [],
    2: [],
    3: [],
    4: [2],
    5: [1, 3],
    6: [2, 4],
}

def get_allowed_retakes(current_sem):
    """Get allowed retake semesters based on current semester"""
    if current_sem in RETAKE_RULES:
        return RETAKE_RULES[current_sem]
    if current_sem >= 7:
        # S7+ can retake any previous semester
        return list(range(1, current_sem))
    return []

# Create database session
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 80)
print("FIXING RETAKE SEMESTERS DATA")
print("=" * 80)

# Get all student profiles
profiles = db.query(StudentProfile).all()

fixed_count = 0
for profile in profiles:
    if not profile.retake_semesters or len(profile.retake_semesters) == 0:
        continue
    
    current_sem = profile.current_semester or 1
    allowed_retakes = get_allowed_retakes(current_sem)
    current_retakes = profile.retake_semesters or []
    
    # Filter out invalid retakes
    valid_retakes = [r for r in current_retakes if r in allowed_retakes]
    
    if sorted(valid_retakes) != sorted(current_retakes):
        print(f"\n{'='*80}")
        print(f"USER ID: {profile.user_id}")
        print(f"Current Semester: {current_sem}")
        print(f"Allowed Retakes: {allowed_retakes}")
        print(f"BEFORE: retake_semesters = {current_retakes}")
        print(f"AFTER:  retake_semesters = {valid_retakes}")
        
        # Update the profile
        profile.retake_semesters = valid_retakes
        fixed_count += 1
        
        # Now we need to remove enrollments and subjects for invalid retake semesters
        invalid_retakes = [r for r in current_retakes if r not in allowed_retakes]
        
        if invalid_retakes and profile.cursus_id:
            print(f"\nRemoving courses from invalid retake semesters: {invalid_retakes}")
            
            # Get semester IDs for invalid retakes
            invalid_semesters = db.query(Semester).filter(
                Semester.academic_track_id == profile.cursus_id,
                Semester.semester_number.in_(invalid_retakes),
                Semester.is_deleted == False
            ).all()
            invalid_sem_ids = [s.id for s in invalid_semesters]
            
            if invalid_sem_ids:
                # Get courses from these semesters
                invalid_courses = db.query(Course).filter(
                    Course.semester_id.in_(invalid_sem_ids),
                    Course.is_deleted == False
                ).all()
                invalid_course_ids = [c.id for c in invalid_courses]
                
                if invalid_course_ids:
                    # Delete enrollments
                    deleted_enrollments = db.query(StudentCourseEnrollment).filter(
                        StudentCourseEnrollment.user_id == profile.user_id,
                        StudentCourseEnrollment.course_id.in_(invalid_course_ids)
                    ).delete(synchronize_session=False)
                    
                    # Delete subjects
                    deleted_subjects = db.query(Subject).filter(
                        Subject.user_id == profile.user_id,
                        Subject.catalog_course_id.in_(invalid_course_ids)
                    ).delete(synchronize_session=False)
                    
                    print(f"  - Deleted {deleted_enrollments} enrollments")
                    print(f"  - Deleted {deleted_subjects} subjects")

if fixed_count > 0:
    db.commit()
    print(f"\n{'='*80}")
    print(f"[OK] FIXED {fixed_count} PROFILES")
    print("=" * 80)
else:
    print(f"\n{'='*80}")
    print("[OK] ALL PROFILES ARE VALID - NO CHANGES NEEDED")
    print("=" * 80)

db.close()
