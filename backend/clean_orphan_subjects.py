"""
Clean all subjects that don't belong to current or retake semesters
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.student_profile import StudentProfile
from app.models.semester import Semester
from app.models.course import Course
from app.models.subject import Subject
from app.core.config import settings

# Create database session
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 80)
print("CLEANING ORPHAN SUBJECTS")
print("=" * 80)

# Get all student profiles
profiles = db.query(StudentProfile).all()

total_deleted = 0
for profile in profiles:
    if not profile.cursus_id or not profile.current_semester:
        continue
    
    # Expected semester numbers
    expected_semesters = [profile.current_semester] + (profile.retake_semesters or [])
    
    print(f"\n{'='*80}")
    print(f"USER ID: {profile.user_id}")
    print(f"Current Semester: {profile.current_semester}")
    print(f"Retake Semesters: {profile.retake_semesters or []}")
    print(f"Expected Semesters: {expected_semesters}")
    
    # Get valid semester IDs for this profile
    valid_semesters = db.query(Semester).filter(
        Semester.academic_track_id == profile.cursus_id,
        Semester.semester_number.in_(expected_semesters),
        Semester.is_deleted == False
    ).all()
    valid_sem_ids = [s.id for s in valid_semesters]
    
    if not valid_sem_ids:
        print("  ⚠️  No valid semesters found for this profile")
        continue
    
    # Get valid course IDs for these semesters
    valid_courses = db.query(Course).filter(
        Course.semester_id.in_(valid_sem_ids),
        Course.is_deleted == False
    ).all()
    valid_course_ids = {c.id for c in valid_courses}
    
    print(f"Valid Semesters: {[s.semester_number for s in valid_semesters]}")
    print(f"Valid Courses: {len(valid_course_ids)}")
    
    # Get all subjects for this user
    all_subjects = db.query(Subject).filter(
        Subject.user_id == profile.user_id
    ).all()
    
    print(f"Total Subjects: {len(all_subjects)}")
    
    # Find orphan subjects (those not linked to valid courses)
    orphan_subjects = []
    for subj in all_subjects:
        if subj.catalog_course_id:
            if subj.catalog_course_id not in valid_course_ids:
                orphan_subjects.append(subj)
    
    if orphan_subjects:
        print(f"[INFO] Found {len(orphan_subjects)} orphan subjects to delete:")
        
        # Group by semester for reporting
        orphan_by_sem = {}
        for subj in orphan_subjects:
            course = db.query(Course).filter(Course.id == subj.catalog_course_id).first()
            if course:
                semester = db.query(Semester).filter(Semester.id == course.semester_id).first()
                if semester:
                    sem_num = semester.semester_number
                    if sem_num not in orphan_by_sem:
                        orphan_by_sem[sem_num] = []
                    orphan_by_sem[sem_num].append(subj.name)
        
        for sem_num in sorted(orphan_by_sem.keys()):
            print(f"   Semester {sem_num}: {len(orphan_by_sem[sem_num])} subjects")
            for name in orphan_by_sem[sem_num][:2]:
                print(f"     - {name}")
        
        # Delete orphan subjects
        for subj in orphan_subjects:
            db.delete(subj)
        
        total_deleted += len(orphan_subjects)
    else:
        print("[OK] No orphan subjects found")

if total_deleted > 0:
    db.commit()
    print(f"\n{'='*80}")
    print(f"[OK] DELETED {total_deleted} ORPHAN SUBJECTS")
    print("=" * 80)
else:
    print(f"\n{'='*80}")
    print("[OK] NO ORPHAN SUBJECTS FOUND - DATABASE IS CLEAN")
    print("=" * 80)

db.close()
