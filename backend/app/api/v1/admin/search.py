"""
Global Search and Discovery API Endpoint

Provides a single cross-entity full-text search endpoint:

  GET  /api/v1/admin/search  — Search across all curriculum entities

Searched entity types:
  - universities   (name, name_de, description)
  - campuses       (name, name_de, location)
  - programs       (name, name_de, code, description)
  - academic_tracks (name, name_de)
  - semesters      (name, name_de)
  - teaching_units (name, name_de, code)
  - courses        (name, name_de, code, description)

Query strategy:
  - SQL ILIKE (case-insensitive LIKE) for portability across PostgreSQL and SQLite
  - Exact-code matches scored 3, name-start matches scored 2, substring matches scored 1
  - Results grouped by entity type in the response
  - Total execution time measured and returned for performance monitoring (target <1s for 10k entities)

RBAC: All admin roles.

Requirements: 19.1-19.7
"""
import time
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.middleware.rbac import (
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR,
)
from app.models.user import User
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course
from app.schemas.admin import SearchResultItem, SearchResponse

router = APIRouter()

# Maximum results returned per entity type
_MAX_PER_TYPE = 20


# ============================================================================
# GET /api/v1/admin/search  — Global search
# ============================================================================

@router.get(
    "",
    response_model=SearchResponse,
    summary="Global search across entities",
    description=(
        "Search across all curriculum entities using partial text matching (case-insensitive). "
        "Results are grouped by entity type and ranked by relevance "
        "(exact code match > name prefix match > substring match). "
        "At most 20 results per entity type are returned. "
        "All admin roles can access this endpoint."
    ),
)
async def global_search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query (min 2 characters)"),
    entity_types: Optional[str] = Query(
        None,
        description=(
            "Comma-separated list of entity types to search. "
            "Leave empty to search all types. "
            "Valid values: universities, campuses, programs, tracks, semesters, teaching_units, courses"
        ),
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full-text search across all curriculum entity types.

    Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7

    Query Parameters:
    - **q**: Search query string (minimum 2 characters).
    - **entity_types**: Optional comma-separated list to restrict search scope.

    Returns:
        SearchResponse with results_by_type dict and total_hits count.
        Includes search duration in milliseconds.

    Raises:
        403: If user does not have any admin role.
        400: If an invalid entity type is provided.
    """
    await _require_admin(current_user, db)

    # Determine which entity types to search
    all_types = [
        "universities", "campuses", "programs", "tracks",
        "semesters", "teaching_units", "courses",
    ]

    if entity_types:
        requested = [t.strip().lower() for t in entity_types.split(",") if t.strip()]
        invalid = [t for t in requested if t not in all_types]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity types: {', '.join(invalid)}. Valid: {', '.join(all_types)}",
            )
        search_types = requested
    else:
        search_types = all_types

    pattern = f"%{q}%"
    start_time = time.perf_counter()

    results_by_type: dict = {}
    total_hits = 0

    # ---- Universities ----
    if "universities" in search_types:
        hits = _search_model(
            db, University, q, pattern,
            name_field="name", name_de_field="name_de",
            extra_fields={"description": "description"},
        )
        if hits:
            results_by_type["universities"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Campuses ----
    if "campuses" in search_types:
        hits = _search_model(
            db, Campus, q, pattern,
            name_field="name", name_de_field="name_de",
            extra_fields={"description": "location"},
        )
        if hits:
            results_by_type["campuses"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Programs ----
    if "programs" in search_types:
        hits = _search_model(
            db, StudyProgram, q, pattern,
            name_field="name", name_de_field="name_de",
            code_field="code",
            extra_fields={"description": "description"},
        )
        if hits:
            results_by_type["programs"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Academic Tracks ----
    if "tracks" in search_types:
        hits = _search_model(
            db, AcademicTrack, q, pattern,
            name_field="name", name_de_field="name_de",
        )
        if hits:
            results_by_type["tracks"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Semesters ----
    if "semesters" in search_types:
        hits = _search_model(
            db, Semester, q, pattern,
            name_field="name", name_de_field="name_de",
        )
        if hits:
            results_by_type["semesters"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Teaching Units ----
    if "teaching_units" in search_types:
        hits = _search_model(
            db, TeachingUnit, q, pattern,
            name_field="name", name_de_field="name_de",
            code_field="code",
        )
        if hits:
            results_by_type["teaching_units"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    # ---- Courses ----
    if "courses" in search_types:
        hits = _search_model(
            db, Course, q, pattern,
            name_field="name", name_de_field="name_de",
            code_field="code",
            extra_fields={"description": "description"},
            is_deleted_field="is_deleted",
        )
        if hits:
            results_by_type["courses"] = [h.model_dump() for h in hits]
            total_hits += len(hits)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return SearchResponse(
        query=q,
        total_hits=total_hits,
        results_by_type=results_by_type,
        search_duration_ms=duration_ms,
    )


# ============================================================================
# Helpers
# ============================================================================

def _search_model(
    db: Session,
    model,
    query: str,
    pattern: str,
    name_field: str,
    name_de_field: Optional[str] = None,
    code_field: Optional[str] = None,
    extra_fields: Optional[dict] = None,
    is_deleted_field: Optional[str] = "is_deleted",
) -> List[SearchResultItem]:
    """
    Search a SQLAlchemy model using ILIKE pattern matching on the relevant text fields.

    Relevance scoring:
      - Code exact match  → 3
      - Name starts-with  → 2
      - Substring match   → 1

    Args:
        db: SQLAlchemy session.
        model: ORM model class.
        query: Raw user query string.
        pattern: ILIKE pattern (%query%).
        name_field: Column name for the primary name field.
        name_de_field: Column name for the German name field.
        code_field: Column name for a code field (optional).
        extra_fields: Dict of {schema_field: model_field} for extra text to search.
        is_deleted_field: Column name for soft-delete flag (None to skip filter).

    Returns:
        Sorted list of SearchResultItem objects (best relevance first).
    """
    entity_type = model.__tablename__

    # Build WHERE conditions
    conditions = []
    name_col = getattr(model, name_field, None)
    if name_col is not None:
        conditions.append(name_col.ilike(pattern))

    if name_de_field:
        name_de_col = getattr(model, name_de_field, None)
        if name_de_col is not None:
            conditions.append(name_de_col.ilike(pattern))

    if code_field:
        code_col = getattr(model, code_field, None)
        if code_col is not None:
            conditions.append(code_col.ilike(pattern))

    if extra_fields:
        for _, model_attr in extra_fields.items():
            col = getattr(model, model_attr, None)
            if col is not None:
                conditions.append(col.ilike(pattern))

    if not conditions:
        return []

    db_query = db.query(model).filter(or_(*conditions))

    # Apply soft-delete filter if applicable
    if is_deleted_field:
        del_col = getattr(model, is_deleted_field, None)
        if del_col is not None:
            db_query = db_query.filter(del_col == False)

    rows = db_query.limit(_MAX_PER_TYPE).all()

    results = []
    q_lower = query.lower()

    for row in rows:
        name = getattr(row, name_field, "") or ""
        name_de = getattr(row, name_de_field, None) if name_de_field else None
        code = getattr(row, code_field, None) if code_field else None
        description = None
        if extra_fields:
            for schema_key, model_attr in extra_fields.items():
                if schema_key == "description":
                    description = getattr(row, model_attr, None)
                    break

        # Relevance scoring
        relevance = 1
        match_field = name_field
        name_lower = name.lower()

        if code and code.lower() == q_lower:
            relevance = 3
            match_field = code_field
        elif name_lower.startswith(q_lower):
            relevance = 2
            match_field = name_field
        elif name_de and name_de.lower().startswith(q_lower):
            relevance = 2
            match_field = name_de_field

        # Truncate long descriptions
        if description and len(description) > 120:
            description = description[:117] + "..."

        results.append(SearchResultItem(
            entity_type=entity_type,
            id=row.id,
            name=name,
            name_de=name_de,
            code=code,
            description=description,
            match_field=match_field,
            relevance=relevance,
        ))

    # Sort by relevance descending, then name ascending
    results.sort(key=lambda r: (-r.relevance, r.name.lower()))
    return results


async def _require_admin(user: User, db: Session) -> None:
    """Raise 403 if the user does not hold any admin role."""
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole

    allowed = [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN, ROLE_PROGRAM_COORDINATOR]
    role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id)
        .join(AdminRole)
        .filter(AdminRole.name.in_(allowed), AdminRole.is_active == True)
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: admin role required",
        )
