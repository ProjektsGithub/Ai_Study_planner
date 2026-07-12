"""
Study Plan API endpoints

Generation is ASYNCHRONOUS:
  POST /generate       → returns {task_id, status:"pending"} immediately (202)
  GET  /generate/status/{task_id} → poll until status "done" or "error"

All other endpoints remain synchronous (they are fast DB operations).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import asyncio

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.study_plan import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    StudyPlanResponse,
    StudyPlanHistoryResponse
)
from app.schemas.session import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse
)
from app.services.study_plan_service import StudyPlanService
from app.services.session_edit_service import SessionEditService
from app.services.plan_optimizer_service import plan_optimizer_service

router = APIRouter(prefix="/study-plans", tags=["study-plans"])

# ── In-memory task store ──────────────────────────────────────────────────────
# {task_id: {status, result, error, created_at, user_id}}
_tasks: dict = {}
_TASK_TTL = timedelta(minutes=10)


def _cleanup_old_tasks():
    cutoff = datetime.utcnow() - _TASK_TTL
    expired = [k for k, v in _tasks.items() if v["created_at"] < cutoff]
    for k in expired:
        del _tasks[k]


async def _run_generation(
    task_id: str,
    user_id: int,
    week_start,
    force_regenerate: bool,
    db: Session,
):
    """Background coroutine: AI plan generation (30-120s). Never blocks HTTP."""
    _tasks[task_id]["status"] = "running"
    try:
        service = StudyPlanService(db)
        success, result = await service.generate_plan(
            user_id=user_id,
            week_start=week_start,
            force_regenerate=force_regenerate,
        )
        if success:
            _tasks[task_id]["status"] = "done"
            _tasks[task_id]["result"] = result
        else:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["error"] = result.get("message", "Generation failed")
    except Exception as e:
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["error"] = str(e)


# ── Generation endpoints ──────────────────────────────────────────────────────

@router.post("/generate", status_code=202)
async def generate_study_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start AI plan generation asynchronously — returns immediately.

    Poll **GET /study-plans/generate/status/{task_id}** every 3-5 seconds.

    - **week_start**: Monday date (YYYY-MM-DD)
    - **force_regenerate**: Skip cache
    """
    _cleanup_old_tasks()
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "user_id": current_user.id,
    }
    # asyncio.create_task() schedules the coroutine on the RUNNING event loop.
    # This is the correct way to run async background work in FastAPI.
    asyncio.create_task(_run_generation(task_id, current_user.id, request.week_start, request.force_regenerate, db))
    return {"task_id": task_id, "status": "pending"}


@router.post("/regenerate", status_code=202)
async def regenerate_study_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate the current active plan asynchronously — returns immediately.

    Same polling pattern as /generate:
    Poll **GET /study-plans/generate/status/{task_id}** every 3-5 seconds.
    """
    from app.services.study_plan_service import StudyPlanService
    from datetime import date

    # Get the current plan's week_start so we regenerate the same week
    service = StudyPlanService(db)
    current = service.get_current_plan(current_user.id)
    if current:
        week_start = current.get("week_start") or date.today().strftime("%Y-%m-%d")
    else:
        week_start = date.today().strftime("%Y-%m-%d")

    _cleanup_old_tasks()
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "user_id": current_user.id,
    }
    asyncio.create_task(_run_generation(task_id, current_user.id, week_start, True, db))
    return {"task_id": task_id, "status": "pending"}


# ── SSE Streaming endpoint ────────────────────────────────────────────────────

@router.post("/stream")
async def stream_study_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a study plan and stream the AI output token-by-token via SSE.

    The HTTP connection stays alive for the entire generation — no timeout.
    The frontend reads a `text/event-stream` response.

    SSE events:
      - `{"type": "status",  "status": "preparing|generating|saving"}`
      - `{"type": "token",   "text": "..."}`   ← one per AI token
      - `{"type": "done",    "plan": {...}}`    ← final plan (after DB save)
      - `{"type": "error",   "message": "..."}`
    """
    from app.services.ai_service import AIService
    from app.services.planning_engine import PlanningEngine
    from app.services.session_edit_service import SessionEditService
    from app.services.validation_service import ValidationService
    from app.models.student_profile import StudentProfile
    from datetime import date as _date
    import json as _json

    def _sse(payload: dict) -> str:
        return f"data: {_json.dumps(payload, ensure_ascii=False)}\n\n"

    async def event_stream():
        try:
            # ── 1. Build planning data (fast DB reads) ───────────────
            yield _sse({"type": "status", "status": "preparing"})

            engine = PlanningEngine(current_user.id, db)
            planning_data = engine.generate_planning_data(db=db)

            # Snapshot subject name→id mapping NOW before the long stream
            # (SQLAlchemy objects may expire during the async wait)
            subject_list_snapshot = list(engine.subjects)

            profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == current_user.id
            ).first()
            if not profile:
                yield _sse({"type": "error", "message": "Student profile not found"})
                return

            profile_context = {
                "semester_start_date": profile.semester_start_date.isoformat() if profile.semester_start_date else None,
                "semester_end_date":   profile.semester_end_date.isoformat()   if profile.semester_end_date   else None,
                "exam_period_start":   profile.exam_period_start.isoformat()   if profile.exam_period_start   else None,
                "total_course_hours_per_week": profile.total_course_hours_per_week,
                "other_commitments_hours":     profile.other_commitments_hours,
                "preferred_study_time":        profile.preferred_study_time,
                "preferred_session_duration":  profile.preferred_session_duration,
                "study_pace":                  profile.study_pace,
            }
            weekly_goal = profile.weekly_study_goal or 20.0
            preferences = profile.preferences or {}

            # ── 2. Stream AI generation ───────────────────────────────
            ai_service = AIService(db)
            plan_data = None

            async for chunk in ai_service.generate_study_plan_stream(
                planning_data=planning_data,
                weekly_study_goal=weekly_goal,
                user_preferences=preferences,
                user_id=current_user.id,
                profile_context=profile_context,
            ):
                # Parse the SSE chunk to intercept the final 'done' event
                if chunk.startswith("data:"):
                    raw = chunk[len("data:"):].strip().rstrip("\n")
                    try:
                        evt = _json.loads(raw)
                        if evt.get("type") == "done":
                            plan_data = evt.get("plan")
                            # Don't yield yet — save to DB first
                            continue
                    except Exception:
                        pass
                # Forward every other event (status, token, error) to client
                yield chunk

            if plan_data is None:
                yield _sse({"type": "error", "message": "AI generation produced no plan"})
                return

            # ── 3. Validate + save to DB ─────────────────────────────
            yield _sse({"type": "status", "status": "saving"})

            service = StudyPlanService(db)
            # NOTE: force_regenerate logic (superseding old plans) is handled
            # internally by _save_plan_to_database — no need to do it here.

            save_result = service._save_plan_to_database(
                user_id=current_user.id,
                week_start=request.week_start,
                plan_data=plan_data,
                subjects=subject_list_snapshot,
            )

            if not save_result.get("success"):
                # _save_plan_to_database already called db.rollback() internally
                yield _sse({"type": "error", "message": save_result.get("message", "Save failed")})
                return

            # NOTE: do NOT call db.commit() here — _save_plan_to_database already committed

            saved_plan = service.get_current_plan(current_user.id)
            yield _sse({"type": "done", "plan": saved_plan})

        except Exception as exc:
            import traceback
            print(f"[STREAM ENDPOINT] Unhandled error: {exc}")
            traceback.print_exc()
            # ⚠️ CRITICAL: rollback the session so the connection is returned
            # to the pool in a clean state — without this, the next request
            # reusing this connection gets 'InFailedSqlTransaction'
            try:
                db.rollback()
            except Exception:
                pass
            yield _sse({"type": "error", "message": str(exc)})



    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )



@router.get("/generate/status/{task_id}")
def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Poll generation status.

    Returns one of:
    - `{status: "pending"}` — queued
    - `{status: "running"}` — AI is generating
    - `{status: "done", plan: {...}}` — success
    - `{status: "error", error: "..."}` — failed
    """
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired (max 10 min)")
    if task["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    response = {"task_id": task_id, "status": task["status"]}
    if task["status"] == "done" and task["result"]:
        response["plan"] = task["result"]
    if task["status"] == "error":
        response["error"] = task["error"]
    return response


# ── Read endpoints ────────────────────────────────────────────────────────────

@router.get("/current", response_model=Optional[StudyPlanResponse])
def get_current_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current active study plan for the authenticated user."""
    service = StudyPlanService(db)
    plan = service.get_current_plan(current_user.id)
    if not plan:
        return None
    return StudyPlanResponse(**plan)


@router.get("/history", response_model=StudyPlanHistoryResponse)
def get_plan_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated history of all study plans."""
    service = StudyPlanService(db)
    result = service.get_plan_history(user_id=current_user.id, page=page, page_size=20)
    return StudyPlanHistoryResponse(**result)


@router.get("/{plan_id}", response_model=StudyPlanResponse)
def get_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a study plan by its UUID."""
    service = StudyPlanService(db)
    plan = service.get_plan_by_id(plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study plan not found")
    return StudyPlanResponse(**plan)


@router.post("/{plan_id}/restore", response_model=GeneratePlanResponse)
def restore_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restore a previous study plan."""
    service = StudyPlanService(db)
    success, result = service.restore_plan(plan_id=plan_id, user_id=current_user.id)
    if not success:
        error_type = result.get("error", "unknown_error")
        if error_type == "plan_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message"))
    return GeneratePlanResponse(**result)


# ── Session editing endpoints ─────────────────────────────────────────────────

@router.post("/{plan_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def add_session(
    plan_id: str,
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new session to a study plan."""
    service = SessionEditService(db)
    success, result = service.add_session(plan_id=plan_id, user_id=current_user.id, session_data=request.model_dump())
    if not success:
        error_type = result.get("error", "unknown_error")
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
        elif error_type in ["validation_error", "session_limit_exceeded"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message"))
    return SessionResponse(**result["session"])


@router.put("/{plan_id}/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    plan_id: str,
    session_id: int,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing session."""
    service = SessionEditService(db)
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    success, result = service.update_session(plan_id=plan_id, session_id=session_id, user_id=current_user.id, update_data=update_data)
    if not success:
        error_type = result.get("error", "unknown_error")
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
        elif error_type == "validation_error":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message"))
    return SessionResponse(**result["session"])


@router.delete("/{plan_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    plan_id: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a session from a study plan."""
    service = SessionEditService(db)
    success, result = service.delete_session(plan_id=plan_id, session_id=session_id, user_id=current_user.id)
    if not success:
        error_type = result.get("error", "unknown_error")
        if error_type in ["plan_not_found", "session_not_found"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message"))
    try:
        plan_optimizer_service.trigger_regeneration(
            db=db, user_id=current_user.id,
            modification_type="session_delete", session_id=session_id, reason="Session deleted",
        )
    except Exception:
        pass
    return None


@router.post("/{plan_id}/sessions/{session_id}/complete", response_model=SessionResponse)
def mark_session_complete(
    plan_id: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a study session as complete."""
    result = plan_optimizer_service.update_progress_and_recalculate(
        db=db, user_id=current_user.id, session_id=session_id,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    service = SessionEditService(db)
    session_obj = service.get_session(plan_id=plan_id, session_id=session_id, user_id=current_user.id)
    if session_obj and isinstance(session_obj, dict):
        return SessionResponse(**session_obj)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
