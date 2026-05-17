"""
Session Edit Service - Handles manual editing of study sessions

Validates:
- Subject references
- Time format and logic
- Availability constraints
- Constraint violations
- Session overlaps
- Maximum session limit
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint


class SessionEditService:
    """
    Service for manually editing study sessions with validation.
    """
    
    MAX_SESSIONS_PER_PLAN = 50
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_session(
        self,
        plan_id: int,
        user_id: int,
        session_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Add a new session to a study plan.
        
        Args:
            plan_id: Study plan ID
            user_id: User ID (for authorization)
            session_data: Session data (subject_id, day, start_time, end_time, task_type, notes)
        
        Returns:
            Tuple of (success, result_or_error)
        """
        # Get plan
        plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            )
        ).first()
        
        if not plan:
            return False, {"error": "plan_not_found", "message": "Study plan not found"}
        
        # Check session limit
        session_count = self.db.query(StudySession).filter(
            StudySession.study_plan_id == plan_id
        ).count()
        
        if session_count >= self.MAX_SESSIONS_PER_PLAN:
            return False, {
                "error": "session_limit_exceeded",
                "message": f"Maximum {self.MAX_SESSIONS_PER_PLAN} sessions per plan"
            }
        
        # Validate session data
        is_valid, validation_result = self._validate_session(
            user_id=user_id,
            session_data=session_data,
            plan_id=plan_id,
            exclude_session_id=None
        )
        
        if not is_valid:
            return False, validation_result
        
        # Create session
        try:
            start_time = datetime.strptime(session_data["start_time"], "%H:%M:%S").time()
            end_time = datetime.strptime(session_data["end_time"], "%H:%M:%S").time()
            
            session = StudySession(
                study_plan_id=plan_id,
                subject_id=session_data["subject_id"],
                day=session_data["day"],
                start_time=start_time,
                end_time=end_time,
                task_type=session_data["task_type"],
                notes=session_data.get("notes", "")
            )
            
            self.db.add(session)
            
            # Mark plan as edited
            plan.edited = True
            
            self.db.commit()
            self.db.refresh(session)
            
            # Get subject name
            subject = self.db.query(Subject).filter(Subject.id == session.subject_id).first()
            
            return True, {
                "success": True,
                "session": {
                    "id": session.id,
                    "study_plan_id": session.study_plan_id,
                    "subject_id": session.subject_id,
                    "subject_name": subject.name if subject else "",
                    "day": session.day,
                    "start_time": session.start_time.strftime("%H:%M:%S"),
                    "end_time": session.end_time.strftime("%H:%M:%S"),
                    "task_type": session.task_type,
                    "notes": session.notes
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return False, {
                "error": "database_error",
                "message": f"Failed to create session: {str(e)}"
            }
    
    def update_session(
        self,
        plan_id: int,
        session_id: int,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Update an existing session.
        
        Args:
            plan_id: Study plan ID
            session_id: Session ID
            user_id: User ID (for authorization)
            update_data: Fields to update
        
        Returns:
            Tuple of (success, result_or_error)
        """
        # Get plan and session
        plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            )
        ).first()
        
        if not plan:
            return False, {"error": "plan_not_found", "message": "Study plan not found"}
        
        session = self.db.query(StudySession).filter(
            and_(
                StudySession.id == session_id,
                StudySession.study_plan_id == plan_id
            )
        ).first()
        
        if not session:
            return False, {"error": "session_not_found", "message": "Session not found"}
        
        # Build complete session data for validation
        session_data = {
            "subject_id": update_data.get("subject_id", session.subject_id),
            "day": update_data.get("day", session.day),
            "start_time": update_data.get("start_time", session.start_time.strftime("%H:%M:%S")),
            "end_time": update_data.get("end_time", session.end_time.strftime("%H:%M:%S")),
            "task_type": update_data.get("task_type", session.task_type),
            "notes": update_data.get("notes", session.notes)
        }
        
        # Validate updated session
        is_valid, validation_result = self._validate_session(
            user_id=user_id,
            session_data=session_data,
            plan_id=plan_id,
            exclude_session_id=session_id
        )
        
        if not is_valid:
            return False, validation_result
        
        # Update session
        try:
            if "subject_id" in update_data:
                session.subject_id = update_data["subject_id"]
            if "day" in update_data:
                session.day = update_data["day"]
            if "start_time" in update_data:
                session.start_time = datetime.strptime(update_data["start_time"], "%H:%M:%S").time()
            if "end_time" in update_data:
                session.end_time = datetime.strptime(update_data["end_time"], "%H:%M:%S").time()
            if "task_type" in update_data:
                session.task_type = update_data["task_type"]
            if "notes" in update_data:
                session.notes = update_data["notes"]
            
            # Mark plan as edited
            plan.edited = True
            
            self.db.commit()
            self.db.refresh(session)
            
            # Get subject name
            subject = self.db.query(Subject).filter(Subject.id == session.subject_id).first()
            
            return True, {
                "success": True,
                "session": {
                    "id": session.id,
                    "study_plan_id": session.study_plan_id,
                    "subject_id": session.subject_id,
                    "subject_name": subject.name if subject else "",
                    "day": session.day,
                    "start_time": session.start_time.strftime("%H:%M:%S"),
                    "end_time": session.end_time.strftime("%H:%M:%S"),
                    "task_type": session.task_type,
                    "notes": session.notes
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return False, {
                "error": "database_error",
                "message": f"Failed to update session: {str(e)}"
            }
    
    def delete_session(
        self,
        plan_id: int,
        session_id: int,
        user_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Delete a session from a study plan.
        
        Args:
            plan_id: Study plan ID
            session_id: Session ID
            user_id: User ID (for authorization)
        
        Returns:
            Tuple of (success, result_or_error)
        """
        # Get plan and session
        plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            )
        ).first()
        
        if not plan:
            return False, {"error": "plan_not_found", "message": "Study plan not found"}
        
        session = self.db.query(StudySession).filter(
            and_(
                StudySession.id == session_id,
                StudySession.study_plan_id == plan_id
            )
        ).first()
        
        if not session:
            return False, {"error": "session_not_found", "message": "Session not found"}
        
        # Delete session
        try:
            self.db.delete(session)
            
            # Mark plan as edited
            plan.edited = True
            
            self.db.commit()
            
            return True, {
                "success": True,
                "message": "Session deleted successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            return False, {
                "error": "database_error",
                "message": f"Failed to delete session: {str(e)}"
            }
    
    def _validate_session(
        self,
        user_id: int,
        session_data: Dict[str, Any],
        plan_id: int,
        exclude_session_id: Optional[int]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate session data against all constraints.
        
        Args:
            user_id: User ID
            session_data: Session data to validate
            plan_id: Study plan ID
            exclude_session_id: Session ID to exclude from overlap check (for updates)
        
        Returns:
            Tuple of (is_valid, error_or_empty)
        """
        errors = []
        
        # 1. Validate subject reference
        subject = self.db.query(Subject).filter(
            and_(
                Subject.id == session_data["subject_id"],
                Subject.user_id == user_id
            )
        ).first()
        
        if not subject:
            errors.append("Invalid subject_id: subject not found or doesn't belong to user")
        
        # 2. Parse times
        try:
            start_time = datetime.strptime(session_data["start_time"], "%H:%M:%S").time()
            end_time = datetime.strptime(session_data["end_time"], "%H:%M:%S").time()
        except ValueError:
            errors.append("Invalid time format: must be HH:MM:SS")
            return False, {"error": "validation_error", "message": "; ".join(errors)}
        
        # 3. Validate start < end
        if start_time >= end_time:
            errors.append("start_time must be before end_time")
        
        # 4. Validate session falls within availability
        availabilities = self.db.query(Availability).filter(
            and_(
                Availability.user_id == user_id,
                Availability.day_of_week == session_data["day"]
            )
        ).all()
        
        if not availabilities:
            errors.append(f"No availability defined for {session_data['day']}")
        else:
            in_availability = False
            for avail in availabilities:
                if start_time >= avail.start_time and end_time <= avail.end_time:
                    in_availability = True
                    break
            
            if not in_availability:
                errors.append(f"Session time {start_time}-{end_time} not within any availability on {session_data['day']}")
        
        # 5. Validate doesn't violate constraints
        constraints = self.db.query(Constraint).filter(
            and_(
                Constraint.user_id == user_id,
                Constraint.active == True
            )
        ).all()
        
        for constraint in constraints:
            if constraint.constraint_type == "max_daily_hours":
                # Check daily hours limit
                max_hours = constraint.parameters.get("max_hours")
                
                # Calculate total hours for this day (including this session)
                existing_sessions = self.db.query(StudySession).filter(
                    and_(
                        StudySession.study_plan_id == plan_id,
                        StudySession.day == session_data["day"]
                    )
                ).all()
                
                total_hours = 0
                for sess in existing_sessions:
                    if exclude_session_id and sess.id == exclude_session_id:
                        continue  # Skip the session being updated
                    duration = (
                        datetime.combine(date.today(), sess.end_time) -
                        datetime.combine(date.today(), sess.start_time)
                    ).total_seconds() / 3600
                    total_hours += duration
                
                # Add new session duration
                new_duration = (
                    datetime.combine(date.today(), end_time) -
                    datetime.combine(date.today(), start_time)
                ).total_seconds() / 3600
                total_hours += new_duration
                
                if total_hours > max_hours:
                    errors.append(f"Adding this session would exceed max_daily_hours constraint ({max_hours}h)")
            
            elif constraint.constraint_type == "forbidden_slot":
                # Check if session overlaps with forbidden slot
                params = constraint.parameters
                if params["day_of_week"] == session_data["day"]:
                    forbidden_start = datetime.strptime(params["start_time"], "%H:%M:%S").time()
                    forbidden_end = datetime.strptime(params["end_time"], "%H:%M:%S").time()
                    
                    # Check overlap
                    if start_time < forbidden_end and end_time > forbidden_start:
                        errors.append(f"Session overlaps with forbidden slot on {session_data['day']}")
        
        # 6. Validate doesn't overlap with other sessions
        existing_sessions = self.db.query(StudySession).filter(
            and_(
                StudySession.study_plan_id == plan_id,
                StudySession.day == session_data["day"]
            )
        ).all()
        
        for sess in existing_sessions:
            if exclude_session_id and sess.id == exclude_session_id:
                continue  # Skip the session being updated
            
            # Check overlap
            if start_time < sess.end_time and end_time > sess.start_time:
                errors.append(f"Session overlaps with existing session on {session_data['day']} at {sess.start_time}-{sess.end_time}")
        
        if errors:
            return False, {
                "error": "validation_error",
                "message": "; ".join(errors),
                "errors": errors
            }
        
        return True, {}
