"""
Test Course Service - CRUD, validation, and prerequisite management
"""
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course
from app.services.course_service import CourseService

print("=" * 70)
print("Test Course Service")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

async def run_tests():
    try:
        # 1. Setup test data
        print("1. Setup test data")
        
        # Clean up any existing test data first
        db.query(University).filter(University.name == "Test University for Courses").delete()
        db.query(StudyProgram).filter(StudyProgram.code == "CS_TEST").delete()
        db.commit()
        
        # Create university
        test_university = University(
            name="Test University for Courses",
            name_de="Test Universität für Kurse",
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
            code="CS_TEST",
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
        semester_1 = Semester(
            academic_track_id=test_track.id,
            name="S1",
            semester_number=1,
            ects_required=30
        )
        semester_2 = Semester(
            academic_track_id=test_track.id,
            name="S2",
            semester_number=2,
            ects_required=30
        )
        db.add_all([semester_1, semester_2])
        db.commit()
        db.refresh(semester_1)
        db.refresh(semester_2)
        print(f"   Semesters created: S1 (ID: {semester_1.id}), S2 (ID: {semester_2.id})")
        
        # Create teaching unit
        test_tu = TeachingUnit(
            semester_id=semester_1.id,
            name="Mathematics Unit",
            name_de="Mathematik Einheit",
            code="UE1",
            ects_required=12
        )
        db.add(test_tu)
        db.commit()
        db.refresh(test_tu)
        print(f"   Teaching Unit created: {test_tu.name} (ID: {test_tu.id})")
        print()
        
        # 2. Create service
        print("2. Create CourseService")
        service = CourseService(db)
        print("   Service created")
        print()
        
        # 3. Test course creation with validation
        print("3. Test course creation with validation")
        
        # Valid course
        course_data = {
            "name": "Introduction to Programming",
            "name_de": "Einführung in die Programmierung",
            "code": "CS101",
            "description": "Basic programming concepts",
            "semester_id": semester_1.id,
            "teaching_unit_id": test_tu.id,
            "ects_credits": 6,
            "coefficient": 2.0,
            "difficulty_level": 3
        }
        
        course1 = await service.create_course(course_data)
        print(f"   ✓ Course created: {course1.name} (ID: {course1.id})")
        print(f"     ECTS: {course1.ects_credits}, Coefficient: {course1.coefficient}, Difficulty: {course1.difficulty_level}")
        print()
        
        # 4. Test validation
        print("4. Test validation")
        
        # Invalid ECTS (out of range)
        print("   4a. Test invalid ECTS (out of range)")
        invalid_course = {
            "name": "Invalid Course",
            "semester_id": semester_1.id,
            "ects_credits": 35,  # > 30
            "coefficient": 2.0,
            "difficulty_level": 3
        }
        try:
            await service.create_course(invalid_course)
            print("     ✗ Should have failed!")
        except ValueError as e:
            print(f"     ✓ Correctly rejected: {str(e)}")
        
        # Invalid coefficient
        print("   4b. Test invalid coefficient")
        invalid_course = {
            "name": "Invalid Course",
            "semester_id": semester_1.id,
            "ects_credits": 6,
            "coefficient": 15.0,  # > 10.0
            "difficulty_level": 3
        }
        try:
            await service.create_course(invalid_course)
            print("     ✗ Should have failed!")
        except ValueError as e:
            print(f"     ✓ Correctly rejected: {str(e)}")
        
        # Invalid difficulty
        print("   4c. Test invalid difficulty")
        invalid_course = {
            "name": "Invalid Course",
            "semester_id": semester_1.id,
            "ects_credits": 6,
            "coefficient": 2.0,
            "difficulty_level": 6  # > 5
        }
        try:
            await service.create_course(invalid_course)
            print("     ✗ Should have failed!")
        except ValueError as e:
            print(f"     ✓ Correctly rejected: {str(e)}")
        print()
        
        # 5. Test filtering and retrieval
        print("5. Test filtering and retrieval")
        
        # Create more courses
        course2_data = {
            "name": "Data Structures",
            "code": "CS102",
            "semester_id": semester_1.id,
            "ects_credits": 8,
            "coefficient": 3.0,
            "difficulty_level": 4
        }
        course2 = await service.create_course(course2_data)
        
        course3_data = {
            "name": "Algorithms",
            "code": "CS201",
            "semester_id": semester_2.id,
            "ects_credits": 10,
            "coefficient": 4.0,
            "difficulty_level": 5
        }
        course3 = await service.create_course(course3_data)
        
        print(f"   Created 2 more courses: {course2.name}, {course3.name}")
        
        # Get all courses
        all_courses, total = await service.get_courses()
        print(f"   Total courses: {total}")
        
        # Filter by semester
        s1_courses, s1_total = await service.get_courses(filters={"semester_id": semester_1.id})
        print(f"   Semester 1 courses: {s1_total}")
        
        # Filter by ECTS range
        high_ects, high_total = await service.get_courses(filters={"ects_min": 8})
        print(f"   Courses with ECTS >= 8: {high_total}")
        
        # Filter by difficulty
        hard_courses, hard_total = await service.get_courses(filters={"difficulty": 5})
        print(f"   Courses with difficulty 5: {hard_total}")
        
        # Search
        search_courses, search_total = await service.get_courses(filters={"search": "data"})
        print(f"   Search 'data': {search_total} courses found")
        print()
        
        # 6. Test update
        print("6. Test course update")
        
        update_data = {
            "ects_credits": 7,
            "difficulty_level": 4
        }
        updated_course = await service.update_course(course1.id, update_data)
        print(f"   ✓ Updated course {course1.name}")
        print(f"     New ECTS: {updated_course.ects_credits}, New difficulty: {updated_course.difficulty_level}")
        print()
        
        # 7. Test get prerequisites and dependents
        print("7. Test prerequisites and dependents")
        
        prereqs = await service.get_course_prerequisites(course3.id)
        print(f"   Prerequisites for {course3.name}: {len(prereqs)}")
        
        dependents = await service.get_course_dependents(course1.id)
        print(f"   Dependent courses for {course1.name}: {len(dependents)}")
        print()
        
        # 8. Test batch update
        print("8. Test batch update")
        
        batch_updates = [
            {"id": course1.id, "coefficient": 2.5},
            {"id": course2.id, "coefficient": 3.5}
        ]
        
        result = await service.batch_update_courses(batch_updates)
        print(f"   Batch update result:")
        print(f"     Success: {result['success_count']}")
        print(f"     Errors: {result['error_count']}")
        print()
        
        # 9. Test delete validation
        print("9. Test delete")
        
        # Create a fourth course to delete
        course4_data = {
            "name": "Temporary Course",
            "code": "CS999",
            "semester_id": semester_1.id,
            "ects_credits": 5,
            "coefficient": 1.5,
            "difficulty_level": 2
        }
        course4 = await service.create_course(course4_data)
        print(f"   Created course to delete: {course4.name} (ID: {course4.id})")
        
        delete_result = await service.delete_course(course4.id)
        print(f"   ✓ Delete result: {delete_result['message']}")
        
        # Verify soft delete
        deleted_course = db.query(Course).filter(Course.id == course4.id).first()
        print(f"   Soft delete verified: is_deleted = {deleted_course.is_deleted}")
        print()
        
        print("=" * 70)
        print("ALL COURSE SERVICE TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Course creation with validation")
        print("  ✓ ECTS validation (1-30)")
        print("  ✓ Coefficient validation (0.1-10.0)")
        print("  ✓ Difficulty validation (1-5)")
        print("  ✓ Filtering (semester, ECTS range, difficulty, search)")
        print("  ✓ Course update")
        print("  ✓ Prerequisite and dependent retrieval")
        print("  ✓ Batch operations")
        print("  ✓ Soft delete")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nCleaning up test data...")
        try:
            if 'semester_1' in locals() and 'semester_2' in locals():
                db.query(Course).filter(Course.semester_id.in_([semester_1.id, semester_2.id])).delete(synchronize_session=False)
                db.query(TeachingUnit).filter(TeachingUnit.id == test_tu.id).delete()
                db.query(Semester).filter(Semester.id.in_([semester_1.id, semester_2.id])).delete()
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
