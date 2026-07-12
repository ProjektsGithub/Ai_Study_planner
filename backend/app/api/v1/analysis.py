"""
Analysis API Endpoints

GET  /api/v1/analysis/risk              — risk scores for all enrolled courses
GET  /api/v1/analysis/risk/{course_id}  — risk score for a single course
GET  /api/v1/analysis/priorities        — priority scores sorted desc
GET  /api/v1/analysis/failed-courses    — failed courses with days_since_failure
GET  /api/v1/analysis/blockers          — prerequisite blockers
POST /api/v1/analysis/recalculate       — force recalculation of all scores

Requirements: 16.9, 16.10, 16.11, 16.13–16.17, 19.2, 19.3, 19.7
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.analysis import (
    RiskScoreResponse,
    RiskScoreListResponse,
    PriorityScoreResponse,
    PriorityScoreListResponse,
    FailedCourseListResponse,
    PrerequisiteBlockerResponse,
)
from app.schemas.auth import MessageResponse
from app.services.risk_analysis_service import risk_analysis_service
from app.services.priority_service import priority_service
from app.services.failed_course_service import failed_course_service

router = APIRouter(prefix="/analysis", tags=["Academic Analysis"])


# ------------------------------------------------------------------
# Risk Scores
# ------------------------------------------------------------------

@router.get(
    "/risk",
    response_model=RiskScoreListResponse,
    summary="Get risk scores for all enrolled courses",
)
async def get_all_risk_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculate and return risk scores for all courses the student has grades for.

    Risk levels: **high** | **medium** | **low**
    Results sorted: high → medium → low.

    Each entry includes a **factors** breakdown explaining the risk level.
    """
    scores = risk_analysis_service.calculate_all_risk_scores(db, current_user.id)
    return RiskScoreListResponse(risk_scores=scores, total=len(scores))


@router.get(
    "/risk/{course_id}",
    response_model=RiskScoreResponse,
    summary="Get risk score for a specific course",
)
async def get_course_risk_score(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculate and return the risk score for a single course.

    Returns 404 if no grade data exists for this course.
    """
    return risk_analysis_service.calculate_risk_score(db, current_user.id, course_id)


# ------------------------------------------------------------------
# Priority Scores
# ------------------------------------------------------------------

@router.get(
    "/priorities",
    response_model=PriorityScoreListResponse,
    summary="Get priority scores for all enrolled courses",
)
async def get_all_priorities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculate priority scores for all enrolled courses, sorted descending.

    Formula weights: ECTS 30% + coefficient 15% + exam proximity 25%
                     + current grade 20% + difficulty 10%
    Bonuses: +15 for failed courses, +10 for prerequisite blockers.

    Each entry includes:
    - **priority_score** (0–100)
    - **recommended_weekly_hours**
    - **success_probability** (0–100%)
    - **risk_level**
    - **factors** breakdown
    """
    scores = priority_service.calculate_all_priorities(db, current_user.id)
    return PriorityScoreListResponse(priorities=scores, total=len(scores))


# ------------------------------------------------------------------
# Failed Courses
# ------------------------------------------------------------------

@router.get(
    "/failed-courses",
    response_model=FailedCourseListResponse,
    summary="Get all failed courses",
)
async def get_failed_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all courses with validation_status='failed'.

    Each entry includes:
    - **attempt_count**: number of failed attempts
    - **days_since_first_failure**: days elapsed since first failed attempt
    - **is_prerequisite_blocker**: whether this course blocks other courses
    - **blocks_courses**: list of course names being blocked
    """
    courses = failed_course_service.get_failed_courses(db, current_user.id)
    return FailedCourseListResponse(failed_courses=courses, total=len(courses))


@router.get(
    "/blockers",
    response_model=List[PrerequisiteBlockerResponse],
    summary="Get prerequisite blockers",
)
async def get_prerequisite_blockers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return failed courses that are blocking progression to other courses.

    Sorted by **blocker_impact** descending (most blocking first).
    """
    return failed_course_service.identify_prerequisite_blockers(db, current_user.id)


# ------------------------------------------------------------------
# Force recalculation
# ------------------------------------------------------------------

@router.post(
    "/recalculate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Force recalculation of all analysis scores",
)
async def recalculate_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force recalculation of risk scores, priority scores, and ECTS progression.

    Useful after bulk grade imports or when data seems stale.
    """
    try:
        # Recalculate risk scores
        risk_analysis_service.calculate_all_risk_scores(db, current_user.id)
        # Recalculate priority scores
        priority_service.calculate_all_priorities(db, current_user.id)
        # Recalculate ECTS
        from app.services.ects_service import ects_service
        ects_service.calculate_progression(db, current_user.id)
    except Exception as exc:
        return {"message": f"Partial recalculation completed with warnings: {exc}"}

    return {"message": "All analysis scores recalculated successfully"}
