"""
Student Course Enrollment API

Endpoints:
  GET  /api/v1/enrollments/my-courses   — catalog courses for the student's semester (+ enrollment status)
  GET  /api/v1/enrollments              — list the student's current enrollments
  POST /api/v1/enrollments              — create or update an enrollment (upsert)
  DELETE /api/v1/enrollments/{course_id} — remove an enrollment
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_course_enrollment import StudentCourseEnrollment
from app.models.course import Course
from app.models.teaching_unit import TeachingUnit
from app.models.semester import Semester
from app.models.academic_track import AcademicTrack
from app.schemas.enrollment import (
    EnrollmentUpsert,
    EnrollmentResponse,
    CatalogCourseResponse,
    SemesterCoursesResponse,
    TeachingUnitBrief,
)
from datetime import datetime, timezone
from app.services.enrollment_sync_service import sync_enrollment_to_subject, remove_subject_for_enrollment

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ---------------------------------------------------------------------------
# GET /api/v1/enrollments/my-courses
# ---------------------------------------------------------------------------

@router.get("/my-courses", response_model=SemesterCoursesResponse)
async def get_my_semester_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all courses for the student's current semester from the admin catalog,
    enriched with the student's enrollment status if they have already enrolled.

    Also returns courses from any retake semesters (German Wiederholung system)
    stored in profile.retake_semesters.

    Requires the student to have an academic profile with cursus_id and current_semester set.
    """
    # 1. Load student profile
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic profile not found. Please complete your preferences first.",
        )

    if not profile.cursus_id or not profile.current_semester:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please set your academic track (cursus) and current semester in Preferences first.",
        )

    # 2. Resolve current semester
    semester = (
        db.query(Semester)
        .filter(
            Semester.academic_track_id == profile.cursus_id,
            Semester.semester_number == profile.current_semester,
            Semester.is_deleted == False,
        )
        .first()
    )

    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No semester S{profile.current_semester} found for your academic track. "
                "Please contact your administrator."
            ),
        )

    # 3. Load all courses for the current semester (with teaching unit)
    courses = (
        db.query(Course)
        .options(joinedload(Course.teaching_unit))
        .filter(
            Course.semester_id == semester.id,
            Course.is_deleted == False,
        )
        .order_by(Course.teaching_unit_id, Course.name)
        .all()
    )

    # 4. Load retake semester courses (German Wiederholung system)
    retake_semester_numbers = profile.retake_semesters or []
    # course_id -> retake_semester_number mapping
    retake_course_map: dict[int, int] = {}

    if retake_semester_numbers:
        retake_semesters_db = (
            db.query(Semester)
            .filter(
                Semester.academic_track_id == profile.cursus_id,
                Semester.semester_number.in_(retake_semester_numbers),
                Semester.is_deleted == False,
            )
            .all()
        )
        for retake_sem in retake_semesters_db:
            retake_courses = (
                db.query(Course)
                .options(joinedload(Course.teaching_unit))
                .filter(
                    Course.semester_id == retake_sem.id,
                    Course.is_deleted == False,
                )
                .order_by(Course.teaching_unit_id, Course.name)
                .all()
            )
            for rc in retake_courses:
                # Avoid duplicates (if a course appears in both current and retake)
                if not any(c.id == rc.id for c in courses):
                    retake_course_map[rc.id] = retake_sem.semester_number
                    courses.append(rc)

    # 5. Load student enrollments for all course IDs
    course_ids = [c.id for c in courses]
    enrollments = {}
    if course_ids:
        rows = (
            db.query(StudentCourseEnrollment)
            .filter(
                StudentCourseEnrollment.user_id == current_user.id,
                StudentCourseEnrollment.course_id.in_(course_ids),
            )
            .all()
        )
        enrollments = {e.course_id: e for e in rows}

    # 6. Build response
    course_responses = []
    for c in courses:
        enrollment = enrollments.get(c.id)
        tu = c.teaching_unit
        is_retake = c.id in retake_course_map
        retake_sem_num = retake_course_map.get(c.id)

        course_responses.append(
            CatalogCourseResponse(
                id=c.id,
                name=c.name,
                code=c.code,
                description=c.description,
                ects_credits=c.ects_credits,
                coefficient=c.coefficient,
                difficulty_level=c.difficulty_level,
                teaching_unit_id=c.teaching_unit_id,
                teaching_unit=TeachingUnitBrief(
                    id=tu.id,
                    name=tu.name,
                    code=tu.code,
                    ects_required=tu.ects_required,
                ) if tu else None,
                enrollment_id=enrollment.id if enrollment else None,
                enrollment_status=enrollment.status if enrollment else None,
                priority_override=enrollment.priority_override if enrollment else None,
                personal_notes=enrollment.personal_notes if enrollment else None,
                is_retake=is_retake,
                retake_semester_number=retake_sem_num,
            )
        )

    # Resolve cursus name
    track = db.query(AcademicTrack).filter(AcademicTrack.id == profile.cursus_id).first()
    cursus_name = track.name if track else f"Track #{profile.cursus_id}"

    return SemesterCoursesResponse(
        semester_id=semester.id,
        semester_name=semester.name,
        semester_number=semester.semester_number,
        cursus_name=cursus_name,
        total_courses=len(courses),
        enrolled_courses=len(enrollments),
        courses=course_responses,
        retake_semesters=retake_semester_numbers,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/enrollments
# ---------------------------------------------------------------------------

@router.get("", response_model=List[EnrollmentResponse])
async def list_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all enrollment records for the authenticated student."""
    rows = (
        db.query(StudentCourseEnrollment)
        .filter(StudentCourseEnrollment.user_id == current_user.id)
        .all()
    )
    return rows


# ---------------------------------------------------------------------------
# POST /api/v1/enrollments  — upsert
# ---------------------------------------------------------------------------

@router.post("", response_model=EnrollmentResponse)
async def upsert_enrollment(
    data: EnrollmentUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create or update a course enrollment.
    If the student already has an enrollment for this course_id, it is updated.
    """
    # Validate the course exists and is not deleted
    course = db.query(Course).filter(
        Course.id == data.course_id,
        Course.is_deleted == False,
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {data.course_id} not found.",
        )

    # Upsert
    enrollment = db.query(StudentCourseEnrollment).filter(
        StudentCourseEnrollment.user_id == current_user.id,
        StudentCourseEnrollment.course_id == data.course_id,
    ).first()

    if enrollment:
        # Update existing
        enrollment.status = data.status
        enrollment.priority_override = data.priority_override
        enrollment.personal_notes = data.personal_notes
        enrollment.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        enrollment = StudentCourseEnrollment(
            user_id=current_user.id,
            course_id=data.course_id,
            status=data.status,
            priority_override=data.priority_override,
            personal_notes=data.personal_notes,
        )
        db.add(enrollment)

    db.commit()
    db.refresh(enrollment)

    # --- Sync to subjects table so the AI planner sees the change ---
    # Re-fetch course with all fields (already loaded above)
    sync_enrollment_to_subject(db, enrollment, course)

    return enrollment


# ---------------------------------------------------------------------------
# DELETE /api/v1/enrollments/{course_id}
# ---------------------------------------------------------------------------

@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
async def remove_enrollment(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an enrollment (resets course to 'not selected')."""
    enrollment = db.query(StudentCourseEnrollment).filter(
        StudentCourseEnrollment.user_id == current_user.id,
        StudentCourseEnrollment.course_id == course_id,
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    db.delete(enrollment)
    db.commit()

    # --- Remove the mirrored Subject from AI planning ---
    remove_subject_for_enrollment(db, current_user.id, course_id)

    return {"message": "Enrollment removed successfully."}
