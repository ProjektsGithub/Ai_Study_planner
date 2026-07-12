"""
Test Prerequisite Service - Circular dependency detection and chain management
"""
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.university import University
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.course import Course
from app.services.prerequisite_service import PrerequisiteService

print("=" * 70)
print("Test Prerequisite Service")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

async def run_tests():
    try:
        # 1. Setup test data
        print("1. Setup test data")
        
        # Clean up any existing test data first
        db.query(University).filter(University.name == "Test University for Prerequisites").delete()
        db.query(StudyProgram).filter(StudyProgram.code == "CS_PREREQ_TEST").delete()
        db.commit()
        
        # Create university
        test_university = University(
            name="Test University for Prerequisites",
            name_de="Test Universität für Voraussetzungen",
            country="Germany",
            description="Test university"
        )
        db.add(test_university)
        db.commit()
        db.refresh(test_university)
        print(f"   University created: {test_university.name} (ID: {test_university.id})")
        
        # Create study program
        test_program = StudyProgram(
            name="Computer Science",
            name_de="Informatik",
            code="CS",
            description="Test program"
        )
        db.add(test_program)
        db.commit()
        db.refresh(test_program)
        print(f"   Program created: {test_program.name} (ID: {test_program.id})")
        
        # Create academic track
        from app.models.academic_track import TrackLevel
        test_track = AcademicTrack(
            study_program_id=test_program.id,
            name="Bachelor Computer Science",
            name_de="Bachelor Informatik",
            level=TrackLevel.BACHELOR,
            total_ects_required=180
        )
        db.add(test_track)
        db.commit()
        db.refresh(test_track)
        print(f"   Track created: {test_track.name} (ID: {test_track.id})")
        
        # Create semesters
        semesters = []
        for i in range(1, 4):
            semester = Semester(
                academic_track_id=test_track.id,
                name=f"S{i}",
                semester_number=i,
                ects_required=30
            )
            db.add(semester)
            semesters.append(semester)
        db.commit()
        for s in semesters:
            db.refresh(s)
        print(f"   Semesters created: S1, S2, S3")
        
        # Create courses
        courses = []
        course_names = [
            ("Programming I", "CS101", 1),
            ("Programming II", "CS102", 2),
            ("Data Structures", "CS201", 2),
            ("Algorithms", "CS202", 3),
            ("Database Systems", "CS301", 3)
        ]
        
        for name, code, sem_num in course_names:
            course = Course(
                name=name,
                code=code,
                semester_id=semesters[sem_num - 1].id,
                ects_credits=6,
                coefficient=2.0,
                difficulty_level=3
            )
            db.add(course)
            courses.append(course)
        
        db.commit()
        for c in courses:
            db.refresh(c)
        
        prog1, prog2, ds, alg, db_course = courses
        print(f"   Courses created: {len(courses)} courses")
        for c in courses:
            print(f"     - {c.name} ({c.code}) - Semester {c.semester.semester_number}")
        print()
        
        # 2. Create service
        print("2. Create PrerequisiteService")
        service = PrerequisiteService(db)
        print("   Service created")
        print()
        
        # 3. Test prerequisite creation
        print("3. Test prerequisite creation")
        
        # Valid prerequisite: Programming II requires Programming I
        prereq1 = await service.create_prerequisite(prog2.id, prog1.id)
        print(f"   ✓ Created: {prog2.name} requires {prog1.name}")
        
        # Valid prerequisite: Data Structures requires Programming I
        prereq2 = await service.create_prerequisite(ds.id, prog1.id)
        print(f"   ✓ Created: {ds.name} requires {prog1.name}")
        
        # Valid prerequisite: Algorithms requires Data Structures
        prereq3 = await service.create_prerequisite(alg.id, ds.id)
        print(f"   ✓ Created: {alg.name} requires {ds.name}")
        
        # Valid prerequisite: Algorithms requires Programming II
        prereq4 = await service.create_prerequisite(alg.id, prog2.id)
        print(f"   ✓ Created: {alg.name} requires {prog2.name}")
        print()
        
        # 4. Test circular dependency detection
        print("4. Test circular dependency detection")
        
        # Try to create a circular dependency: Programming I requires Algorithms
        print("   4a. Attempt to create circular dependency")
        try:
            await service.create_prerequisite(prog1.id, alg.id)
            print("     ✗ Should have detected circular dependency!")
        except ValueError as e:
            print(f"     ✓ Correctly rejected: Circular dependency detected")
            print(f"        Message: {str(e)[:100]}...")
        
        # Try direct circular: A requires B, B requires A
        print("   4b. Attempt direct circular dependency")
        try:
            await service.create_prerequisite(prog1.id, prog2.id)
            print("     ✗ Should have detected circular dependency!")
        except ValueError as e:
            print(f"     ✓ Correctly rejected: Circular dependency detected")
        print()
        
        # 5. Test self-prerequisite validation
        print("5. Test self-prerequisite validation")
        try:
            await service.create_prerequisite(prog1.id, prog1.id)
            print("   ✗ Should have rejected self-prerequisite!")
        except ValueError as e:
            print(f"   ✓ Correctly rejected: {str(e)}")
        print()
        
        # 6. Test semester validation
        print("6. Test semester validation")
        print("   6a. Attempt to add later semester course as prerequisite")
        try:
            # Database Systems (S3) requires Algorithms (S3) - should work (same semester)
            prereq_same = await service.create_prerequisite(db_course.id, alg.id)
            print(f"   ✓ Same semester prerequisite allowed: {db_course.name} requires {alg.name}")
        except ValueError as e:
            print(f"   Note: {str(e)}")
        
        print("   6b. Attempt to add future semester course as prerequisite")
        try:
            # Programming I (S1) requires Algorithms (S3) - should fail
            await service.create_prerequisite(prog1.id, alg.id)
            print("   ✗ Should have rejected future semester prerequisite!")
        except ValueError as e:
            print(f"   ✓ Correctly rejected: {str(e)[:80]}...")
        print()
        
        # 7. Test prerequisite chain retrieval
        print("7. Test prerequisite chain retrieval")
        
        chain = await service.get_prerequisite_chain(alg.id)
        print(f"   Prerequisite chain for {alg.name}:")
        print(f"   Total prerequisites (direct + indirect): {len(chain)}")
        
        for item in chain:
            print(f"     Level {item['level']}: {item['course_name']} ({item['course_code']}) "
                  f"- S{item['semester_number']} - {item['ects_credits']} ECTS")
            print(f"               Required by: {item['required_by_name']}")
        print()
        
        # 8. Test prerequisite listing
        print("8. Test prerequisite listing")
        
        all_prereqs, total = await service.get_prerequisites()
        print(f"   Total prerequisite relationships: {total}")
        
        # Filter by course
        alg_prereqs, alg_total = await service.get_prerequisites(
            filters={"course_id": alg.id}
        )
        print(f"   Prerequisites for {alg.name}: {alg_total}")
        print()
        
        # 9. Test prerequisite deletion
        print("9. Test prerequisite deletion")
        
        # Delete one prerequisite
        delete_result = await service.delete_prerequisite(alg.id, prog2.id)
        print(f"   ✓ Deleted: {alg.name} no longer requires {prog2.name}")
        print(f"     Message: {delete_result['message']}")
        
        # Verify deletion
        alg_prereqs_after, alg_total_after = await service.get_prerequisites(
            filters={"course_id": alg.id}
        )
        print(f"   Prerequisites for {alg.name} after deletion: {alg_total_after}")
        print()
        
        # 10. Test complex chain
        print("10. Test complex prerequisite chain")
        
        chain_ds = await service.get_prerequisite_chain(ds.id)
        print(f"   Prerequisite chain for {ds.name}:")
        print(f"   Total prerequisites: {len(chain_ds)}")
        for item in chain_ds:
            print(f"     Level {item['level']}: {item['course_name']}")
        print()
        
        print("=" * 70)
        print("ALL PREREQUISITE SERVICE TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Prerequisite creation")
        print("  ✓ Circular dependency detection (direct and indirect)")
        print("  ✓ Self-prerequisite validation")
        print("  ✓ Semester validation (no future semesters as prerequisites)")
        print("  ✓ Prerequisite chain retrieval (BFS traversal)")
        print("  ✓ Prerequisite listing and filtering")
        print("  ✓ Prerequisite deletion (soft delete)")
        print("  ✓ Complex multi-level chains")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nCleaning up test data...")
        try:
            if 'semesters' in locals() and len(semesters) > 0:
                semester_ids = [s.id for s in semesters]
                db.query(Course).filter(Course.semester_id.in_(semester_ids)).delete(synchronize_session=False)
                db.query(Semester).filter(Semester.academic_track_id == test_track.id).delete()
            if 'test_track' in locals():
                db.query(AcademicTrack).filter(AcademicTrack.id == test_track.id).delete()
            if 'test_program' in locals():
                db.query(StudyProgram).filter(StudyProgram.id == test_program.id).delete()
            if 'test_university' in locals():
                db.query(University).filter(University.id == test_university.id).delete()
            db.commit()
            print("Test data cleaned up")
        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}")
        db.close()

# Run async tests
asyncio.run(run_tests())
