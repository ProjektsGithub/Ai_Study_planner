"""
Super Admin Platform Client
===========================

Provides read-only access to university/program/course reference data
stored in the Super Admin Platform tables (same PostgreSQL database).

All functions accept a SQLAlchemy ``Session`` so they participate in
the caller's unit-of-work and do NOT open separate connections.

24-hour in-memory cache
-----------------------
Reference data (universities, filieres, cursus, semester structures,
course details) is cached per process for 24 hours to avoid redundant
DB round-trips.  The cache is keyed by function name + argument tuple.

Cache is invalidated:
  - automatically after TTL_SECONDS (86 400 s)
  - manually via ``invalidate_cache()`` (call when Super Admin notifies
    that reference data changed)

Error handling
--------------
All functions wrap DB errors and return empty/None results gracefully
so the student-facing features remain available even when the admin
schema is temporarily unavailable.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------
# Structure: { cache_key: (payload, expiry_timestamp) }
_cache: Dict[str, Tuple[Any, float]] = {}
TTL_SECONDS: int = 86_400  # 24 hours


def _cache_get(key: str) -> Optional[Any]:
    """Return cached value if still valid, else None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    payload, expiry = entry
    if time.time() > expiry:
        del _cache[key]
        return None
    return payload


def _cache_set(key: str, payload: Any) -> None:
    """Store payload in cache with a 24-hour TTL."""
    _cache[key] = (payload, time.time() + TTL_SECONDS)


def invalidate_cache(key: Optional[str] = None) -> None:
    """
    Invalidate cache entries.

    Args:
        key: If provided, only that key is removed.
             If None, the entire cache is cleared.
    """
    if key is None:
        _cache.clear()
        logger.info("[SuperAdminClient] Entire cache invalidated")
    elif key in _cache:
        del _cache[key]
        logger.info("[SuperAdminClient] Cache key '%s' invalidated", key)


# ---------------------------------------------------------------------------
# University helpers
# ---------------------------------------------------------------------------

def fetch_universities(db: Session) -> List[Dict]:
    """
    Return all active (non-deleted) universities.

    Returns:
        List of dicts with keys: id, name, code (country used as code fallback).

    Requirements: 17.2
    """
    cache_key = "universities"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.university import University
        rows = (
            db.query(University)
            .filter(University.is_deleted == False)  # noqa: E712
            .order_by(University.name)
            .all()
        )
        result = [
            {
                "id": u.id,
                "name": u.name,
                # Universities don't have a 'code' column — use name as fallback
                "code": None,
            }
            for u in rows
        ]
        _cache_set(cache_key, result)
        logger.debug("[SuperAdminClient] fetch_universities: %d results", len(result))
        return result
    except SQLAlchemyError as exc:
        logger.error("[SuperAdminClient] fetch_universities failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Filière (StudyProgram) helpers
# ---------------------------------------------------------------------------

def fetch_filieres(db: Session, university_id: int) -> List[Dict]:
    """
    Return all study programs (filières) linked to a university.

    Args:
        university_id: ID of the university.

    Returns:
        List of dicts: id, name, code, university_id.

    Requirements: 17.3
    """
    cache_key = f"filieres:{university_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.study_program import StudyProgram, university_programs
        rows = (
            db.query(StudyProgram)
            .join(
                university_programs,
                StudyProgram.id == university_programs.c.study_program_id,
            )
            .filter(
                university_programs.c.university_id == university_id,
                StudyProgram.is_deleted == False,  # noqa: E712
            )
            .order_by(StudyProgram.name)
            .all()
        )
        result = [
            {
                "id": sp.id,
                "name": sp.name,
                "code": sp.code,
                "university_id": university_id,
            }
            for sp in rows
        ]
        _cache_set(cache_key, result)
        logger.debug(
            "[SuperAdminClient] fetch_filieres(university_id=%d): %d results",
            university_id,
            len(result),
        )
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_filieres(university_id=%d) failed: %s",
            university_id,
            exc,
        )
        return []


# ---------------------------------------------------------------------------
# Cursus (AcademicTrack) helpers
# ---------------------------------------------------------------------------

def fetch_cursus(db: Session, filiere_id: int) -> List[Dict]:
    """
    Return all academic tracks (cursus) for a study program (filière).

    Args:
        filiere_id: ID of the study program.

    Returns:
        List of dicts: id, name, level, filiere_id, total_ects.

    Requirements: 17.4
    """
    cache_key = f"cursus:{filiere_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.academic_track import AcademicTrack
        rows = (
            db.query(AcademicTrack)
            .filter(
                AcademicTrack.study_program_id == filiere_id,
                AcademicTrack.is_deleted == False,  # noqa: E712
            )
            .order_by(AcademicTrack.name)
            .all()
        )
        result = [
            {
                "id": t.id,
                "name": t.name,
                "code": None,
                "filiere_id": filiere_id,
                "total_ects": float(t.total_ects_required) if t.total_ects_required else None,
                "level": t.level.value if t.level else None,
            }
            for t in rows
        ]
        _cache_set(cache_key, result)
        logger.debug(
            "[SuperAdminClient] fetch_cursus(filiere_id=%d): %d results",
            filiere_id,
            len(result),
        )
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_cursus(filiere_id=%d) failed: %s",
            filiere_id,
            exc,
        )
        return []


# ---------------------------------------------------------------------------
# Semester structure helpers
# ---------------------------------------------------------------------------

def fetch_semester_structure(db: Session, cursus_id: int) -> Optional[Dict]:
    """
    Return the complete semester structure for a cursus (AcademicTrack).

    Args:
        cursus_id: ID of the academic track.

    Returns:
        Dict with keys: cursus_id, cursus_name, total_ects, semesters (list).
        None if cursus not found.

    Requirements: 17.5
    """
    cache_key = f"semester_structure:{cursus_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.academic_track import AcademicTrack
        from app.models.semester import Semester

        track = (
            db.query(AcademicTrack)
            .filter(
                AcademicTrack.id == cursus_id,
                AcademicTrack.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if track is None:
            logger.warning(
                "[SuperAdminClient] fetch_semester_structure: cursus_id=%d not found",
                cursus_id,
            )
            return None

        semesters = (
            db.query(Semester)
            .filter(
                Semester.academic_track_id == cursus_id,
                Semester.is_deleted == False,  # noqa: E712
            )
            .order_by(Semester.semester_number)
            .all()
        )

        result = {
            "cursus_id": cursus_id,
            "cursus_name": track.name,
            "total_ects": float(track.total_ects_required) if track.total_ects_required else None,
            "semesters": [
                {
                    "id": s.id,
                    "number": s.semester_number,
                    "name": s.name,
                    "ects_required": float(s.ects_required) if s.ects_required else None,
                }
                for s in semesters
            ],
        }
        _cache_set(cache_key, result)
        logger.debug(
            "[SuperAdminClient] fetch_semester_structure(cursus_id=%d): %d semesters",
            cursus_id,
            len(semesters),
        )
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_semester_structure(cursus_id=%d) failed: %s",
            cursus_id,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Course detail helpers
# ---------------------------------------------------------------------------

def fetch_course_details(db: Session, course_id: int) -> Optional[Dict]:
    """
    Return full course details including ECTS, coefficient, difficulty,
    prerequisites, and UE (teaching unit) assignment.

    Args:
        course_id: ID of the course in the Super Admin Platform.

    Returns:
        Dict with course fields, or None if not found.

    Requirements: 17.6
    """
    cache_key = f"course:{course_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.course import Course
        from app.models.prerequisite import Prerequisite

        course = (
            db.query(Course)
            .filter(
                Course.id == course_id,
                Course.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if course is None:
            return None

        # Fetch prerequisite course IDs via raw SQL (avoids mapper config issue
        # with the incomplete back_populates on Prerequisite <-> Course)
        from sqlalchemy import text
        prereq_rows = db.execute(
            text("SELECT prerequisite_course_id FROM prerequisites WHERE course_id = :cid"),
            {"cid": course_id}
        ).fetchall()
        prerequisite_ids = [r[0] for r in prereq_rows]

        dependent_rows = db.execute(
            text("SELECT course_id FROM prerequisites WHERE prerequisite_course_id = :cid"),
            {"cid": course_id}
        ).fetchall()
        dependent_ids = [r[0] for r in dependent_rows]

        result = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "ects_credits": float(course.ects_credits) if course.ects_credits else 0.0,
            "coefficient": float(course.coefficient) if course.coefficient else 1.0,
            "difficulty_level": course.difficulty_level,
            "semester_id": course.semester_id,
            "teaching_unit_id": course.teaching_unit_id,
            "prerequisite_ids": prerequisite_ids,   # must pass these first
            "dependent_course_ids": dependent_ids,  # this blocks these if failed
        }
        _cache_set(cache_key, result)
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_course_details(course_id=%d) failed: %s",
            course_id,
            exc,
        )
        return None


def fetch_courses_in_semester(db: Session, semester_id: int) -> List[Dict]:
    """
    Return all courses in a given semester (used by ECTS and priority services).

    Args:
        semester_id: Semester ID from the Super Admin Platform.

    Returns:
        List of course detail dicts.
    """
    cache_key = f"courses_in_semester:{semester_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.course import Course
        rows = (
            db.query(Course)
            .filter(
                Course.semester_id == semester_id,
                Course.is_deleted == False,  # noqa: E712
            )
            .order_by(Course.name)
            .all()
        )
        result = [
            {
                "id": c.id,
                "name": c.name,
                "code": c.code,
                "ects_credits": float(c.ects_credits) if c.ects_credits else 0.0,
                "coefficient": float(c.coefficient) if c.coefficient else 1.0,
                "difficulty_level": c.difficulty_level,
                "semester_id": c.semester_id,
                "teaching_unit_id": c.teaching_unit_id,
            }
            for c in rows
        ]
        _cache_set(cache_key, result)
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_courses_in_semester(semester_id=%d) failed: %s",
            semester_id,
            exc,
        )
        return []


def fetch_total_ects_for_cursus(db: Session, cursus_id: int) -> Optional[float]:
    """
    Return total ECTS required for graduation for a cursus.

    Args:
        cursus_id: ID of the academic track.

    Returns:
        Total ECTS as float, or None if cursus not found.

    Requirements: 17.5 (subset — used by ECTS Service)
    """
    cache_key = f"total_ects:{cursus_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from app.models.academic_track import AcademicTrack
        track = (
            db.query(AcademicTrack)
            .filter(
                AcademicTrack.id == cursus_id,
                AcademicTrack.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if track is None:
            return None
        result = float(track.total_ects_required) if track.total_ects_required else None
        _cache_set(cache_key, result)
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[SuperAdminClient] fetch_total_ects_for_cursus(cursus_id=%d) failed: %s",
            cursus_id,
            exc,
        )
        return None


def fetch_prerequisite_map(db: Session) -> Dict[int, List[int]]:
    """
    Build a complete prerequisite map for all courses.

    Returns:
        Dict mapping course_id → list of prerequisite_course_ids.
        e.g. {42: [10, 15]} means course 42 requires courses 10 and 15.

    Used by: FailedCourseService to detect prerequisite blockers.
    Requirements: 10.7
    """
    cache_key = "prerequisite_map"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        # Use raw SQL to avoid ORM mapper configuration issues with
        # the incomplete back_populates on the Prerequisite <-> Course relationship.
        from sqlalchemy import text
        rows = db.execute(
            text("SELECT course_id, prerequisite_course_id FROM prerequisites")
        ).fetchall()
        result: Dict[int, List[int]] = {}
        for row in rows:
            result.setdefault(row[0], []).append(row[1])
        _cache_set(cache_key, result)
        logger.debug("[SuperAdminClient] fetch_prerequisite_map: %d entries", len(result))
        return result
    except SQLAlchemyError as exc:
        logger.error("[SuperAdminClient] fetch_prerequisite_map failed: %s", exc)
        return {}
