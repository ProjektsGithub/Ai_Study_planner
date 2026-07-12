"""
Study Plan Service - Orchestrates the complete plan generation workflow

Workflow:
1. Retrieve user data (profile, subjects, availabilities, constraints)
2. Run PlanningEngine to get valid slots and priorities
3. Call AIService to generate plan
4. Validate with ValidationService
5. Save to database (StudyPlan + StudySessions)
6. Implement caching and error handling
"""
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.services.planning_engine import PlanningEngine
from app.services.ai_service import AIService
from app.services.validation_service import ValidationService


class StudyPlanService:
    """
    Service for generating and managing study plans.
    Orchestrates the complete workflow from data retrieval to database persistence.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService(db)
        self.validation_service = ValidationService(db)
        
        # Simple in-memory cache: {cache_key: (plan_data, timestamp)}
        self._cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._max_cache_size = 100
    
    async def generate_plan(
        self,
        user_id: int,
        week_start: date,
        force_regenerate: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a new study plan for the specified week.
        
        Args:
            user_id: User ID
            week_start: Start date of the week (should be Monday)
            force_regenerate: Skip cache and force new generation
        
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Step 1: Retrieve user data
            user_data = self._retrieve_user_data(user_id)
            if not user_data["success"]:
                return False, user_data
            
            profile = user_data["profile"]
            subjects = user_data["subjects"]
            availabilities = user_data["availabilities"]
            constraints = user_data["constraints"]
            
            # Validate we have minimum required data
            if not subjects:
                return False, {
                    "error": "no_subjects",
                    "message": "No subjects found. Please add at least one subject before generating a plan."
                }
            
            if not availabilities:
                return False, {
                    "error": "no_availabilities",
                    "message": "No availabilities found. Please add your available time slots before generating a plan."
                }
            
            # Step 2: Check cache (unless force_regenerate)
            if not force_regenerate:
                cache_key = self._compute_cache_key(user_id, week_start, subjects, availabilities, constraints)
                cached_plan = self._get_from_cache(cache_key)
                if cached_plan:
                    return True, {
                        "success": True,
                        "plan": cached_plan,
                        "from_cache": True
                    }
            
            # Step 3: Run PlanningEngine logic
            valid_slots = self._construct_valid_slots_from_data(availabilities, constraints)
            
            if not valid_slots:
                return False, {
                    "error": "no_valid_slots",
                    "message": "No valid time slots available after applying constraints. Please adjust your availabilities or constraints."
                }
            
            priorities = self._calculate_priorities_from_data(subjects, week_start)
            constraint_info = self._validate_constraints_from_data(constraints)
            
            # Step 4: Call AI Service
            planning_data = {
                "valid_slots": [slot.to_dict() for slot in valid_slots],
                "subject_priorities": [p.to_dict() for p in priorities],
                "constraints": constraint_info
            }
            
            # Prepare profile context for AI
            profile_context = {
                "semester_start_date": profile.semester_start_date.isoformat() if profile.semester_start_date else None,
                "semester_end_date": profile.semester_end_date.isoformat() if profile.semester_end_date else None,
                "exam_period_start": profile.exam_period_start.isoformat() if profile.exam_period_start else None,
                "total_course_hours_per_week": profile.total_course_hours_per_week,
                "other_commitments_hours": profile.other_commitments_hours,
                "preferred_study_time": profile.preferred_study_time,
                "preferred_session_duration": profile.preferred_session_duration,
                "study_pace": profile.study_pace
            }
            
            # Run async AI service call
            ai_result = await self.ai_service.generate_study_plan(
                planning_data=planning_data,
                weekly_study_goal=profile.weekly_study_goal,
                user_preferences=profile.preferences or {},
                user_id=user_id,
                profile_context=profile_context
            )
            
            if not ai_result["success"]:
                return False, {
                    "error": "ai_generation_failed",
                    "message": ai_result.get("error", "AI service failed to generate plan"),
                    "details": ai_result
                }
            
            plan_data = ai_result["plan"]
            
            # Step 5: Validate plan
            is_valid, validation_result = self.validation_service.validate_plan(
                plan_data=plan_data,
                valid_slots=valid_slots,
                subjects=subjects,
                weekly_study_goal=profile.weekly_study_goal,
                constraints=constraint_info,
                auto_correct=True
            )
            
            if not is_valid:
                return False, {
                    "error": "validation_failed",
                    "message": "Generated plan failed validation",
                    "validation_errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
            
            # Get corrected plan
            corrected_plan = validation_result["plan"]
            corrections_made = validation_result.get("corrections_made", [])
            warnings = validation_result.get("warnings", [])
            
            # Step 6: Save to database
            save_result = self._save_plan_to_database(
                user_id=user_id,
                week_start=week_start,
                plan_data=corrected_plan,
                subjects=subjects
            )
            
            if not save_result["success"]:
                return False, save_result
            
            # Step 7: Cache the result
            if not force_regenerate:
                self._add_to_cache(cache_key, corrected_plan)
            
            # Step 8: Return success response
            return True, {
                "success": True,
                "plan_id": save_result["plan_id"],
                "plan": corrected_plan,
                "corrections_made": corrections_made,
                "warnings": warnings,
                "from_cache": False,
                "generation_time": ai_result.get("generation_time", 0)
            }
            
        except Exception as e:
            return False, {
                "error": "unexpected_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
    
    def get_plan_by_id(self, plan_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a study plan by its UUID.
        
        Args:
            plan_id: Plan UUID
            user_id: User ID (for authorization)
        
        Returns:
            Plan data or None if not found
        """
        plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.plan_id == plan_id,
                StudyPlan.user_id == user_id
            )
        ).first()
        
        if not plan:
            return None
        
        return self._format_plan_response(plan)
    
    def get_current_plan(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the current active plan for the user.
        
        Args:
            user_id: User ID
        
        Returns:
            Current plan data or None if no active plan
        """
        # Get the most recent plan with status 'generated'
        plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.user_id == user_id,
                StudyPlan.status == "generated"
            )
        ).order_by(StudyPlan.created_at.desc()).first()
        
        if not plan:
            return None
        
        return self._format_plan_response(plan)
    
    def get_plan_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated history of all study plans for the user.
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            Dictionary with plans, pagination info
        """
        from sqlalchemy import func
        
        # Get total count
        total_count = self.db.query(func.count(StudyPlan.id)).filter(
            StudyPlan.user_id == user_id
        ).scalar()
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        offset = (page - 1) * page_size
        
        # Get plans for current page
        plans = self.db.query(StudyPlan).filter(
            StudyPlan.user_id == user_id
        ).order_by(StudyPlan.created_at.desc()).limit(page_size).offset(offset).all()
        
        # Format plan items
        plan_items = []
        for plan in plans:
            # Calculate session count and total hours
            session_count = len(plan.sessions)
            total_hours = 0
            for session in plan.sessions:
                duration = (
                    datetime.combine(date.today(), session.end_time) -
                    datetime.combine(date.today(), session.start_time)
                ).total_seconds() / 3600
                total_hours += duration
            
            plan_items.append({
                "plan_id": plan.plan_id,
                "week_start": plan.week_start.isoformat(),
                "status": plan.status,
                "edited": plan.edited,
                "created_at": plan.created_at.isoformat(),
                "session_count": session_count,
                "total_hours": round(total_hours, 2)
            })
        
        return {
            "plans": plan_items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def restore_plan(
        self,
        plan_id: str,
        user_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Restore a previous study plan by creating a new active plan with the same sessions.
        
        Args:
            plan_id: Plan UUID to restore
            user_id: User ID (for authorization)
        
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Get the plan to restore
            old_plan = self.db.query(StudyPlan).filter(
                and_(
                    StudyPlan.plan_id == plan_id,
                    StudyPlan.user_id == user_id
                )
            ).first()
            
            if not old_plan:
                return False, {
                    "error": "plan_not_found",
                    "message": "Study plan not found"
                }
            
            # Create new plan with same week_start
            new_plan_id = str(uuid.uuid4())
            
            new_plan = StudyPlan(
                plan_id=new_plan_id,
                user_id=user_id,
                week_start=old_plan.week_start,
                status="generated",
                summary=old_plan.summary,
                edited=False  # Reset edited flag
            )
            
            self.db.add(new_plan)
            self.db.flush()  # Get the ID
            
            # Copy all sessions from old plan
            for old_session in old_plan.sessions:
                new_session = StudySession(
                    study_plan_id=new_plan.id,
                    subject_id=old_session.subject_id,
                    day=old_session.day,
                    start_time=old_session.start_time,
                    end_time=old_session.end_time,
                    task_type=old_session.task_type,
                    notes=old_session.notes
                )
                self.db.add(new_session)
            
            # Mark previous active plans for same week as superseded
            self.db.query(StudyPlan).filter(
                and_(
                    StudyPlan.user_id == user_id,
                    StudyPlan.week_start == old_plan.week_start,
                    StudyPlan.status == "generated",
                    StudyPlan.id != new_plan.id
                )
            ).update({"status": "superseded"})
            
            self.db.commit()
            
            # Format response
            plan_data = self._format_plan_response(new_plan)
            
            return True, {
                "success": True,
                "plan_id": new_plan_id,
                "plan": plan_data,
                "from_cache": False,
                "message": f"Plan restored successfully from {old_plan.created_at.strftime('%Y-%m-%d %H:%M')}"
            }
            
        except Exception as e:
            self.db.rollback()
            return False, {
                "error": "restore_failed",
                "message": f"Failed to restore plan: {str(e)}"
            }
    
    def delete_old_plans(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Delete study plans older than the specified retention period.
        This method should be called by a background job.
        
        Args:
            retention_days: Number of days to retain plans (default: 90)
        
        Returns:
            Dictionary with deletion statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count plans to delete
            plans_to_delete = self.db.query(StudyPlan).filter(
                StudyPlan.created_at < cutoff_date
            ).all()
            
            count = len(plans_to_delete)
            
            # Delete plans (sessions will be cascade deleted)
            for plan in plans_to_delete:
                self.db.delete(plan)
            
            self.db.commit()
            
            return {
                "success": True,
                "deleted_count": count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0
            }
    
    def invalidate_user_cache(self, user_id: int):
        """
        Invalidate all cached plans for a user.
        Called when user data changes (subjects, availabilities, constraints).
        
        Args:
            user_id: User ID
        """
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"user_{user_id}_")]
        for key in keys_to_remove:
            del self._cache[key]
    
    def mark_plans_as_outdated(self, user_id: int):
        """
        Mark all future plans as outdated when user data changes.
        
        Args:
            user_id: User ID
        """
        today = date.today()
        self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.user_id == user_id,
                StudyPlan.week_start >= today,
                StudyPlan.status == "generated"
            )
        ).update({"status": "outdated"})
        self.db.commit()
    
    def _retrieve_user_data(self, user_id: int) -> Dict[str, Any]:
        """Retrieve all user data needed for plan generation"""
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "user_not_found", "message": "User not found"}
        
        # Get profile
        profile = self.db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not profile:
            return {"success": False, "error": "profile_not_found", "message": "Student profile not found. Please create your profile first."}
        
        # Get subjects
        subjects = self.db.query(Subject).filter(Subject.user_id == user_id).all()
        
        # Get availabilities
        availabilities = self.db.query(Availability).filter(Availability.user_id == user_id).all()
        
        # Get active constraints
        constraints = self.db.query(Constraint).filter(
            and_(
                Constraint.user_id == user_id,
                Constraint.active == True
            )
        ).all()
        
        return {
            "success": True,
            "user": user,
            "profile": profile,
            "subjects": subjects,
            "availabilities": availabilities,
            "constraints": constraints
        }
    
    def _save_plan_to_database(
        self,
        user_id: int,
        week_start: date,
        plan_data: Dict[str, Any],
        subjects: list
    ) -> Dict[str, Any]:
        """Save generated plan to database"""
        try:
            # Create subject name to ID mapping
            subject_map = {s.name: s.id for s in subjects}
            
            # Generate UUID for plan
            plan_id = str(uuid.uuid4())
            
            # Create StudyPlan record
            study_plan = StudyPlan(
                plan_id=plan_id,
                user_id=user_id,
                week_start=week_start,
                status="generated",
                summary=plan_data.get("reasoning", ""),
                edited=False
            )
            
            self.db.add(study_plan)
            self.db.flush()  # Get the ID without committing
            
            # Create StudySession records
            for session_data in plan_data.get("sessions", []):
                subject_name = session_data.get("subject_name")
                subject_id = subject_map.get(subject_name)
                
                if not subject_id:
                    continue  # Skip if subject not found (shouldn't happen after validation)
                
                # Parse time strings
                start_time = datetime.strptime(session_data.get("start_time"), "%H:%M:%S").time()
                end_time = datetime.strptime(session_data.get("end_time"), "%H:%M:%S").time()
                
                session = StudySession(
                    study_plan_id=study_plan.id,
                    subject_id=subject_id,
                    day=session_data.get("day"),
                    start_time=start_time,
                    end_time=end_time,
                    task_type=session_data.get("task_type"),
                    notes=session_data.get("notes", "")
                )
                
                self.db.add(session)

            # ── Ensure week_start is a real date object (not a string) ─────
            # Pydantic/JSON can pass it as a string; PostgreSQL date column
            # refuses comparison with VARCHAR → explicit cast needed.
            from datetime import date as _date_type
            if isinstance(week_start, str):
                week_start = _date_type.fromisoformat(week_start)

            # Mark previous plans as superseded
            self.db.query(StudyPlan).filter(
                and_(
                    StudyPlan.user_id == user_id,
                    StudyPlan.week_start == week_start,
                    StudyPlan.status == "generated",
                    StudyPlan.id != study_plan.id
                )
            ).update({"status": "superseded"}, synchronize_session="fetch")

            self.db.commit()
            
            # Create notification for plan generation
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(self.db)
            notification_service.create_plan_generated_notification(user_id, study_plan)
            
            return {
                "success": True,
                "plan_id": plan_id
            }
            
        except Exception as e:
            self.db.rollback()
            # Log l'erreur complète pour debug
            import traceback
            print(f"\n[STUDY_PLAN_SERVICE ERROR] Failed to save plan:")
            print(f"Error: {str(e)}")
            print(f"Traceback:")
            traceback.print_exc()
            print(f"Plan data: {plan_data}")
            print("")
            
            return {
                "success": False,
                "error": "database_error",
                "message": f"Failed to save plan to database: {str(e)}"
            }
    
    def _format_plan_response(self, plan: StudyPlan) -> Dict[str, Any]:
        """Format a StudyPlan database record as API response"""
        sessions = []
        for session in plan.sessions:
            sessions.append({
                "id": session.id,
                "subject_id": session.subject_id,
                "subject_name": session.subject.name,
                "day": session.day,
                "start_time": session.start_time.strftime("%H:%M:%S"),
                "end_time": session.end_time.strftime("%H:%M:%S"),
                "task_type": session.task_type,
                "notes": session.notes or ""
            })
        
        # Calculate total hours
        total_hours = 0
        for session in plan.sessions:
            duration = (
                datetime.combine(date.today(), session.end_time) -
                datetime.combine(date.today(), session.start_time)
            ).total_seconds() / 3600
            total_hours += duration
        
        return {
            "plan_id": plan.plan_id,
            "week_start": plan.week_start.isoformat(),
            "status": plan.status,
            "summary": plan.summary or "",
            "edited": plan.edited,
            "created_at": plan.created_at.isoformat(),
            "sessions": sessions,
            "total_hours": round(total_hours, 2)
        }
    
    def _compute_cache_key(
        self,
        user_id: int,
        week_start: date,
        subjects: list,
        availabilities: list,
        constraints: list
    ) -> str:
        """Compute cache key from user data"""
        import hashlib
        import json
        
        # Create deterministic representation
        data = {
            "user_id": user_id,
            "week_start": week_start.isoformat(),
            "subjects": sorted([
                {
                    "name": s.name,
                    "priority": s.priority,
                    "difficulty": s.difficulty,
                    "target_weekly_hours": s.target_weekly_hours,
                    "exam_date": s.exam_date.isoformat() if s.exam_date else None
                }
                for s in subjects
            ], key=lambda x: x["name"]),
            "availabilities": sorted([
                {
                    "day": a.day_of_week,
                    "start": a.start_time.strftime("%H:%M:%S"),
                    "end": a.end_time.strftime("%H:%M:%S")
                }
                for a in availabilities
            ], key=lambda x: (x["day"], x["start"])),
            "constraints": sorted([
                {
                    "type": c.constraint_type,
                    "params": c.parameters
                }
                for c in constraints
            ], key=lambda x: x["type"])
        }
        
        # Compute hash
        json_str = json.dumps(data, sort_keys=True)
        hash_value = hashlib.sha256(json_str.encode()).hexdigest()[:16]
        
        return f"user_{user_id}_week_{week_start.isoformat()}_{hash_value}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get plan from cache if not expired"""
        if cache_key not in self._cache:
            return None
        
        plan_data, timestamp = self._cache[cache_key]
        
        # Check if expired
        if datetime.utcnow() - timestamp > self._cache_ttl:
            del self._cache[cache_key]
            return None
        
        return plan_data
    
    def _add_to_cache(self, cache_key: str, plan_data: Dict[str, Any]):
        """Add plan to cache with LRU eviction"""
        # Simple LRU: remove oldest if at capacity
        if len(self._cache) >= self._max_cache_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[cache_key] = (plan_data, datetime.utcnow())
    
    def _construct_valid_slots_from_data(
        self,
        availabilities: list,
        constraints: list
    ) -> list:
        """Construct valid time slots from availabilities and constraints"""
        from app.services.planning_engine import TimeSlot
        
        if not availabilities:
            return []
        
        # Step 1: Convert availabilities to time slots
        slots = []
        for avail in availabilities:
            slot = TimeSlot(avail.day_of_week, avail.start_time, avail.end_time)
            if slot.duration_minutes >= 15:  # Minimum 15 minutes
                slots.append(slot)
        
        if not slots:
            return []
        
        # Step 2: Remove forbidden slots
        forbidden_constraints = [
            c for c in constraints 
            if c.constraint_type == "forbidden_slot"
        ]
        
        for constraint in forbidden_constraints:
            params = constraint.parameters
            forbidden_slot = TimeSlot(
                params["day_of_week"],
                datetime.strptime(params["start_time"], "%H:%M:%S").time(),
                datetime.strptime(params["end_time"], "%H:%M:%S").time()
            )
            
            # Remove overlapping portions
            slots = self._remove_forbidden_overlap(slots, forbidden_slot)
        
        # Step 3: Filter slots with minimum duration
        valid_slots = [s for s in slots if s.duration_minutes >= 15]
        
        return valid_slots
    
    def _remove_forbidden_overlap(self, slots: list, forbidden) -> list:
        """Remove forbidden slot overlaps from available slots"""
        from app.services.planning_engine import TimeSlot
        
        result = []
        
        for slot in slots:
            if not slot.overlaps_with(forbidden):
                result.append(slot)
            else:
                # Keep the part before forbidden slot
                if slot.start_time < forbidden.start_time:
                    before_slot = TimeSlot(slot.day, slot.start_time, forbidden.start_time)
                    if before_slot.duration_minutes >= 15:
                        result.append(before_slot)
                
                # Keep the part after forbidden slot
                if slot.end_time > forbidden.end_time:
                    after_slot = TimeSlot(slot.day, forbidden.end_time, slot.end_time)
                    if after_slot.duration_minutes >= 15:
                        result.append(after_slot)
        
        return result
    
    def _calculate_priorities_from_data(self, subjects: list, week_start: date) -> list:
        """Calculate subject priorities with weighted scoring"""
        from app.services.planning_engine import SubjectPriority
        
        if not subjects:
            return []
        
        priorities = []
        
        for subject in subjects:
            # Base priority (20% weight): normalize 1-5 to 0-100
            base_score = ((subject.priority - 1) / 4) * 100 * 0.20
            
            # Difficulty (20% weight): normalize 1-5 to 0-100
            difficulty_score = ((subject.difficulty - 1) / 4) * 100 * 0.20
            
            # Exam proximity (40% weight)
            exam_score = self._calculate_exam_proximity_score(subject.exam_date, week_start) * 0.40
            
            # Target hours (20% weight)
            hours_score = min(subject.target_weekly_hours / 20, 1.0) * 100 * 0.20
            
            # Total score
            total_score = base_score + difficulty_score + exam_score + hours_score
            
            priorities.append(SubjectPriority(subject, total_score))
        
        # Sort by priority score (descending)
        priorities.sort(key=lambda x: x.priority_score, reverse=True)
        
        return priorities
    
    def _calculate_exam_proximity_score(self, exam_date: date, reference_date: date) -> float:
        """Calculate exam proximity score (0-100)"""
        if not exam_date:
            return 50.0  # Neutral score for no exam
        
        days_until_exam = (exam_date - reference_date).days
        
        if days_until_exam < 0:
            return 0.0  # Exam already passed
        elif days_until_exam <= 7:
            return 100.0  # Urgent
        elif days_until_exam <= 30:
            return 80.0 + (30 - days_until_exam) * (20.0 / 23)  # 80-100
        elif days_until_exam <= 60:
            return 50.0 + (60 - days_until_exam) * (30.0 / 30)  # 50-80
        else:
            return max(20.0, 50.0 - (days_until_exam - 60) * 0.5)  # Decreasing
    
    def _validate_constraints_from_data(self, constraints: list) -> dict:
        """Validate and format constraints for AI"""
        constraint_info = {
            "max_daily_hours": None,
            "required_breaks": [],
            "fixed_slots": [],
            "forbidden_slots_count": 0
        }
        
        for constraint in constraints:
            if constraint.constraint_type == "max_daily_hours":
                constraint_info["max_daily_hours"] = constraint.parameters.get("max_hours")
            elif constraint.constraint_type == "required_break":
                constraint_info["required_breaks"].append(constraint.parameters)
            elif constraint.constraint_type == "fixed_slot":
                constraint_info["fixed_slots"].append(constraint.parameters)
            elif constraint.constraint_type == "forbidden_slot":
                constraint_info["forbidden_slots_count"] += 1
        
        return constraint_info
