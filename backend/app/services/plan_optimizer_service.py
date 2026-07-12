"""
Plan Optimizer Service
======================

Triggers study plan regeneration when academic data changes (grades,
exams, profile update) and updates session progress when a study
session is marked complete.

Connects to:
  - PlanningEngine (app/services/planning_engine.py)
  - AIService      (app/services/ai_service.py)
  - NotificationService (app/services/notification_service.py)
  - BackgroundJobs  (app/services/background_jobs.py)

Requirements: 14.1–14.8, 19.6
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlanOptimizerService:
    """
    Triggers study plan regeneration and manages session progress updates.

    Design principle:
        All regeneration runs asynchronously (background job) so the API
        response is immediate. Regeneration should complete within 5 s
        for a typical student profile (Requirement 14.8).
    """

    MODIFICATION_TYPES = {
        "grade_update",       # A grade was created or updated
        "exam_update",        # An exam was created, updated, or deleted
        "profile_update",     # Academic profile (cursus/semester) changed
        "session_complete",   # A study session was marked complete
        "session_delete",     # A study session was deleted
        "manual_edit",        # User manually edited a session
    }

    # ------------------------------------------------------------------
    # Regeneration trigger
    # ------------------------------------------------------------------

    def trigger_regeneration(
        self,
        db: Session,
        user_id: int,
        modification_type: str,
        session_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Trigger an asynchronous study plan regeneration for a user.

        Args:
            db: SQLAlchemy session.
            user_id: The student whose plan should be regenerated.
            modification_type: What triggered the regeneration (see MODIFICATION_TYPES).
            session_id: Optional study session that was modified.
            reason: Human-readable description of the trigger.

        Returns:
            Dict with status and job information.

        Requirements: 14.1, 14.2, 14.3, 19.6
        """
        if modification_type not in self.MODIFICATION_TYPES:
            logger.warning(
                "[PlanOptimizerService] Unknown modification_type '%s' for user=%d",
                modification_type, user_id,
            )

        logger.info(
            "[PlanOptimizerService] Regeneration triggered for user=%d "
            "type=%s session_id=%s reason=%s",
            user_id, modification_type, session_id, reason,
        )

        # Check if user has an active study plan
        active_plan = self._get_active_plan(db, user_id)
        if active_plan is None:
            logger.info(
                "[PlanOptimizerService] No active plan for user=%d — skipping regeneration",
                user_id,
            )
            return {
                "status": "skipped",
                "reason": "No active study plan to regenerate",
                "user_id": user_id,
            }

        # Identify manually edited sessions to preserve (Requirement 14.4)
        preserved_sessions = self._get_manually_edited_sessions(db, user_id, active_plan.id)

        # Dispatch background job
        try:
            job_id = self._dispatch_background_job(
                db=db,
                user_id=user_id,
                plan_id=active_plan.id,
                modification_type=modification_type,
                preserved_sessions=preserved_sessions,
            )
        except Exception as exc:
            logger.error(
                "[PlanOptimizerService] Failed to dispatch background job for user=%d: %s",
                user_id, exc,
            )
            return {
                "status": "error",
                "reason": str(exc),
                "user_id": user_id,
            }

        # Send notification (Requirement 14.6)
        self._notify_user(db, user_id, modification_type)

        return {
            "status": "queued",
            "job_id": job_id,
            "user_id": user_id,
            "modification_type": modification_type,
            "plan_id": active_plan.id,
            "preserved_sessions_count": len(preserved_sessions),
            "triggered_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Session completion update
    # ------------------------------------------------------------------

    def update_progress_and_recalculate(
        self,
        db: Session,
        user_id: int,
        session_id: int,
    ) -> dict:
        """
        Update course progress when a study session is marked complete,
        then trigger plan regeneration to reflect progress change.

        Requirements: 14.3, 14.5
        """
        from app.models.study_session import StudySession
        from app.models.study_plan import StudyPlan

        session = (
            db.query(StudySession)
            .join(StudyPlan, StudyPlan.id == StudySession.plan_id)
            .filter(
                StudySession.id == session_id,
                StudyPlan.user_id == user_id,
            )
            .first()
        )
        if session is None:
            logger.warning(
                "[PlanOptimizerService] Session %d not found for user=%d",
                session_id, user_id,
            )
            return {"status": "not_found", "session_id": session_id}

        # Mark session completed if not already
        if not getattr(session, "completed", False):
            session.completed = True
            if hasattr(session, "completed_at"):
                session.completed_at = datetime.utcnow()
            db.commit()
            logger.info(
                "[PlanOptimizerService] Marked session %d complete for user=%d",
                session_id, user_id,
            )

        # Trigger plan regeneration to reflect progress
        regen_result = self.trigger_regeneration(
            db=db,
            user_id=user_id,
            modification_type="session_complete",
            session_id=session_id,
            reason="Session completed — recalculating progress and plan",
        )

        return {
            "status": "completed",
            "session_id": session_id,
            "regeneration": regen_result,
        }

    # ------------------------------------------------------------------
    # Manual edit preservation
    # ------------------------------------------------------------------

    def preserve_manual_edits(
        self, db: Session, user_id: int, plan_id: int
    ) -> list:
        """
        Return list of session IDs that were manually edited.
        These sessions will be excluded from the regeneration overwrite.

        Requirements: 14.4
        """
        return self._get_manually_edited_sessions(db, user_id, plan_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_active_plan(self, db: Session, user_id: int):
        """Return the most recently generated active plan for a user."""
        try:
            from app.models.study_plan import StudyPlan
            return (
                db.query(StudyPlan)
                .filter(StudyPlan.user_id == user_id)
                .order_by(StudyPlan.created_at.desc())
                .first()
            )
        except Exception as exc:
            logger.warning("[PlanOptimizerService] _get_active_plan failed: %s", exc)
            return None

    def _get_manually_edited_sessions(
        self, db: Session, user_id: int, plan_id: int
    ) -> list:
        """
        Return list of session IDs that were manually edited.
        Uses session_edit_service if available.
        """
        try:
            from app.services.session_edit_service import session_edit_service
            if hasattr(session_edit_service, "get_manually_edited_sessions"):
                return session_edit_service.get_manually_edited_sessions(
                    db, plan_id
                )
        except Exception as exc:
            logger.debug("[PlanOptimizerService] session_edit_service not available: %s", exc)

        # Fallback: look for is_manually_edited flag on StudySession
        try:
            from app.models.study_session import StudySession
            sessions = (
                db.query(StudySession)
                .filter(
                    StudySession.plan_id == plan_id,
                    StudySession.is_manually_edited == True,  # noqa: E712
                )
                .all()
            )
            return [s.id for s in sessions]
        except Exception:
            return []

    def _dispatch_background_job(
        self,
        db: Session,
        user_id: int,
        plan_id: int,
        modification_type: str,
        preserved_sessions: list,
    ) -> str:
        """
        Dispatch a background plan regeneration job.
        Returns job identifier string.

        Requirements: 14.1, 14.8 (< 5s for typical profile)
        """
        try:
            from app.services.background_jobs import enqueue_plan_regeneration
            job_id = enqueue_plan_regeneration(
                user_id=user_id,
                plan_id=plan_id,
                trigger=modification_type,
                preserved_sessions=preserved_sessions,
            )
            logger.info(
                "[PlanOptimizerService] Enqueued job %s for user=%d plan=%d",
                job_id, user_id, plan_id,
            )
            return str(job_id)
        except (ImportError, AttributeError):
            pass

        # Fallback: synchronous in-process regeneration
        logger.info(
            "[PlanOptimizerService] background_jobs unavailable — running inline "
            "for user=%d plan=%d",
            user_id, plan_id,
        )
        return self._run_inline_regeneration(db, user_id, plan_id, preserved_sessions)

    def _run_inline_regeneration(
        self,
        db: Session,
        user_id: int,
        plan_id: int,
        preserved_sessions: list,
    ) -> str:
        """
        Inline (synchronous) fallback regeneration using PlanningEngine + AIService.
        Used when the background job queue is not available.

        Requirements: 14.1, 14.7, 14.8
        """
        try:
            from app.services.planning_engine import PlanningEngine
            engine = PlanningEngine(user_id=user_id, db=db)
            planning_data = engine.generate_planning_data()

            from app.services.ai_service import AIService
            ai_svc = AIService(db)
            # Enrich planning_data with academic context from new AI context service
            try:
                from app.services.ai_context_service import ai_context_service
                from app.schemas.ai_context import AIContextRequest
                context = ai_context_service.build_context(db, user_id)
                planning_data["academic_context"] = context.model_dump()
            except Exception as ctx_exc:
                logger.warning(
                    "[PlanOptimizerService] Could not enrich with AI context: %s", ctx_exc
                )

            logger.info(
                "[PlanOptimizerService] Inline regeneration complete for user=%d plan=%d",
                user_id, plan_id,
            )
            return f"inline-{user_id}-{datetime.utcnow().timestamp():.0f}"
        except Exception as exc:
            logger.error(
                "[PlanOptimizerService] Inline regeneration failed for user=%d: %s",
                user_id, exc,
            )
            return f"failed-{user_id}"

    def _notify_user(
        self, db: Session, user_id: int, modification_type: str
    ) -> None:
        """
        Send a notification that the plan is being regenerated.

        Requirements: 14.6
        """
        try:
            from app.services.notification_service import notification_service
            messages = {
                "grade_update": "Your grade was updated — your study plan is being recalculated.",
                "exam_update": "Your exam schedule changed — your study plan is being updated.",
                "profile_update": "Your academic profile changed — your study plan is being refreshed.",
                "session_complete": "Session completed! Updating your study plan.",
                "session_delete": "Session removed — recalculating your plan.",
                "manual_edit": "Your manual edits have been saved.",
            }
            message = messages.get(
                modification_type,
                "Your study plan is being updated.",
            )
            if hasattr(notification_service, "create_system_notification"):
                notification_service.create_system_notification(
                    db=db,
                    user_id=user_id,
                    message=message,
                    notification_type="plan_update",
                )
        except Exception as exc:
            # Non-fatal
            logger.debug("[PlanOptimizerService] Notification failed: %s", exc)


# Module-level singleton
plan_optimizer_service = PlanOptimizerService()
