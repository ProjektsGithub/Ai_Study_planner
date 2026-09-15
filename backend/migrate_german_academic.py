"""
Migration script for German Academic Model & Dynamic TD/TP:
1. Add group_name and is_fixed to class_schedules if not exists.
2. Add selected_td_slot_id and selected_tp_slot_id to student_course_enrollments if not exists.
3. Link class_schedules.course_id to courses.id where course_id is NULL based on track/semester and name/code.
4. Auto-populate group_name (e.g. 'Gruppe 1' / 'Groupe 1') for TD and TP slots if currently NULL.
"""
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.class_schedule import ClassSchedule
from app.models.course import Course

def run_migration():
    print("Running migration for German Academic Model...")
    with engine.begin() as conn:
        # 1. class_schedules columns
        conn.execute(text("""
            ALTER TABLE class_schedules 
            ADD COLUMN IF NOT EXISTS group_name VARCHAR(50) DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS is_fixed BOOLEAN DEFAULT TRUE;
        """))
        print("[OK] class_schedules columns verified/added.")

        # 2. student_course_enrollments columns
        conn.execute(text("""
            ALTER TABLE student_course_enrollments 
            ADD COLUMN IF NOT EXISTS selected_td_slot_id INTEGER REFERENCES class_schedules(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS selected_tp_slot_id INTEGER REFERENCES class_schedules(id) ON DELETE SET NULL;
        """))
        print("[OK] student_course_enrollments columns verified/added.")

    db = SessionLocal()
    try:
        # 3. Link course_id on class_schedules
        schedules = db.query(ClassSchedule).all()
        linked_count = 0
        for s in schedules:
            if s.course_id is None:
                # Clean course name (strip "(Travaux Dirigés)", "(Travaux Pratiques)", "(CM)", etc.)
                clean_name = s.course_name.split('(')[0].strip()
                # Try finding course in same semester
                course = db.query(Course).filter(
                    Course.semester_id == s.semester_id,
                    (Course.name == clean_name) | (Course.code == s.course_code)
                ).first()
                if not course and s.academic_track_id:
                    # Try finding by name across the track
                    course = db.query(Course).filter(
                        Course.name == clean_name
                    ).first()

                if course:
                    s.course_id = course.id
                    linked_count += 1

            # 4. Populate group_name if TD or TP and not set
            if s.session_type in ["TD", "TP"] and not s.group_name:
                s.group_name = "Groupe 1"
                s.is_fixed = False  # TD/TP can be selectable/flexible across groups
            elif s.session_type == "CM":
                s.group_name = "Promotion (Fixe)"
                s.is_fixed = True

        db.commit()
        print(f"[OK] Linked {linked_count} class schedules to courses.")
        print(f"[OK] Total class schedules in DB: {len(schedules)}.")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
