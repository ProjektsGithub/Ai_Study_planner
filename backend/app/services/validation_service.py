"""
Validation Service for AI-generated study plans

Validates plans for:
- JSON schema compliance
- Session validity (in valid slots)
- Constraint violations
- Subject references
- Total hours (goal ± 20% tolerance)

Attempts automatic corrections when possible.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.services.planning_engine import TimeSlot


class ValidationError:
    """Represents a validation error"""
    
    def __init__(self, error_type: str, message: str, session_index: Optional[int] = None):
        self.error_type = error_type
        self.message = message
        self.session_index = session_index
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.error_type,
            "message": self.message,
            "session_index": self.session_index
        }


class ValidationService:
    """
    Service for validating and correcting AI-generated study plans.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
        self.corrections_made: List[str] = []
    
    def validate_plan(
        self,
        plan_data: Dict[str, Any],
        valid_slots: List[TimeSlot],
        subjects: List[Subject],
        weekly_study_goal: float,
        constraints: Dict[str, Any],
        auto_correct: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate AI-generated plan and optionally auto-correct issues.
        
        Args:
            plan_data: AI-generated plan with sessions
            valid_slots: Valid time slots from PlanningEngine
            subjects: List of user subjects
            weekly_study_goal: Target weekly hours
            constraints: Constraint information
            auto_correct: Whether to attempt automatic corrections
        
        Returns:
            Tuple of (is_valid, corrected_plan_or_errors)
        """
        self.errors = []
        self.warnings = []
        self.corrections_made = []
        
        # Step 1: Validate JSON schema
        if not self._validate_schema(plan_data):
            return False, self._build_error_response()
        
        # Step 2: Validate subject references
        subject_map = {s.name: s for s in subjects}
        if not self._validate_subject_references(plan_data, subject_map):
            if not auto_correct:
                return False, self._build_error_response()
            # Try to correct invalid subject references
            plan_data = self._correct_subject_references(plan_data, subject_map)
            # Clear errors after correction
            self.errors = []
        
        # Step 3: Validate sessions are in valid slots
        if not self._validate_sessions_in_slots(plan_data, valid_slots):
            if not auto_correct:
                return False, self._build_error_response()
            # Try to adjust sessions to fit valid slots
            plan_data = self._correct_session_times(plan_data, valid_slots)
            # Clear errors after correction
            self.errors = []
        
        # Step 4: Validate constraint violations
        if not self._validate_constraints(plan_data, constraints):
            if not auto_correct:
                return False, self._build_error_response()
            # Try to fix constraint violations
            plan_data = self._correct_constraint_violations(plan_data, constraints)
            # Clear errors after correction
            self.errors = []
        
        # Step 5: Validate total hours (goal ± 20% tolerance)
        if not self._validate_total_hours(plan_data, weekly_study_goal):
            # This is a warning, not a hard error
            pass
        
        # Step 6: Remove any remaining invalid sessions
        if auto_correct:
            plan_data = self._remove_invalid_sessions(plan_data, valid_slots, subject_map)
        
        # Check if we still have errors after corrections
        if self.errors:
            return False, self._build_error_response()
        
        # Build success response
        return True, {
            "valid": True,
            "plan": plan_data,
            "corrections_made": self.corrections_made,
            "warnings": self.warnings
        }
    
    def _validate_schema(self, plan_data: Dict[str, Any]) -> bool:
        """Validate JSON schema structure"""
        required_fields = ["sessions", "total_hours"]
        
        for field in required_fields:
            if field not in plan_data:
                self.errors.append(ValidationError(
                    "schema_error",
                    f"Missing required field: {field}"
                ))
                return False
        
        if not isinstance(plan_data["sessions"], list):
            self.errors.append(ValidationError(
                "schema_error",
                "Field 'sessions' must be a list"
            ))
            return False
        
        # Validate each session structure
        required_session_fields = ["day", "start_time", "end_time", "subject_name", "task_type"]
        
        for i, session in enumerate(plan_data["sessions"]):
            for field in required_session_fields:
                if field not in session:
                    self.errors.append(ValidationError(
                        "schema_error",
                        f"Session {i}: Missing required field '{field}'",
                        session_index=i
                    ))
                    return False
            
            # Validate task_type
            valid_task_types = ["lecture_review", "exercise_practice", "exam_preparation", "project_work", "reading"]
            if session["task_type"] not in valid_task_types:
                self.errors.append(ValidationError(
                    "schema_error",
                    f"Session {i}: Invalid task_type '{session['task_type']}'. Must be one of {valid_task_types}",
                    session_index=i
                ))
                return False
        
        return True
    
    def _validate_subject_references(
        self, 
        plan_data: Dict[str, Any], 
        subject_map: Dict[str, Subject]
    ) -> bool:
        """Validate that all subject references exist"""
        all_valid = True
        
        for i, session in enumerate(plan_data["sessions"]):
            subject_name = session.get("subject_name")
            if subject_name not in subject_map:
                self.errors.append(ValidationError(
                    "invalid_subject",
                    f"Session {i}: Subject '{subject_name}' not found",
                    session_index=i
                ))
                all_valid = False
        
        return all_valid
    
    def _validate_sessions_in_slots(
        self, 
        plan_data: Dict[str, Any], 
        valid_slots: List[TimeSlot]
    ) -> bool:
        """Validate that all sessions fall within valid time slots"""
        all_valid = True
        
        # Create a map of slots by day
        slots_by_day = {}
        for slot in valid_slots:
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = []
            slots_by_day[slot.day].append(slot)
        
        for i, session in enumerate(plan_data["sessions"]):
            day = session.get("day")
            start_time_str = session.get("start_time")
            end_time_str = session.get("end_time")
            
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
                end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
            except (ValueError, TypeError):
                self.errors.append(ValidationError(
                    "invalid_time_format",
                    f"Session {i}: Invalid time format",
                    session_index=i
                ))
                all_valid = False
                continue
            
            # Check if session is in any valid slot for that day
            if day not in slots_by_day:
                self.errors.append(ValidationError(
                    "invalid_slot",
                    f"Session {i}: No valid slots on {day}",
                    session_index=i
                ))
                all_valid = False
                continue
            
            session_in_valid_slot = False
            for slot in slots_by_day[day]:
                if start_time >= slot.start_time and end_time <= slot.end_time:
                    session_in_valid_slot = True
                    break
            
            if not session_in_valid_slot:
                self.errors.append(ValidationError(
                    "invalid_slot",
                    f"Session {i}: Time {start_time_str}-{end_time_str} not in valid slots for {day}",
                    session_index=i
                ))
                all_valid = False
        
        return all_valid
    
    def _validate_constraints(
        self, 
        plan_data: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> bool:
        """Validate constraint compliance"""
        all_valid = True
        
        # Check max_daily_hours
        if constraints.get("max_daily_hours"):
            max_hours = constraints["max_daily_hours"]
            daily_hours = {}
            
            for session in plan_data["sessions"]:
                day = session.get("day")
                start_time = datetime.strptime(session.get("start_time"), "%H:%M:%S").time()
                end_time = datetime.strptime(session.get("end_time"), "%H:%M:%S").time()
                
                duration_hours = (
                    datetime.combine(datetime.today(), end_time) - 
                    datetime.combine(datetime.today(), start_time)
                ).total_seconds() / 3600
                
                daily_hours[day] = daily_hours.get(day, 0) + duration_hours
            
            for day, hours in daily_hours.items():
                if hours > max_hours:
                    self.errors.append(ValidationError(
                        "constraint_violation",
                        f"{day}: Total hours ({hours:.1f}h) exceeds max_daily_hours ({max_hours}h)"
                    ))
                    all_valid = False
        
        return all_valid
    
    def _validate_total_hours(
        self, 
        plan_data: Dict[str, Any], 
        weekly_study_goal: float
    ) -> bool:
        """Validate total hours is within goal ± 20% tolerance"""
        total_hours = plan_data.get("total_hours", 0)
        
        min_hours = weekly_study_goal * 0.8
        max_hours = weekly_study_goal * 1.2
        
        if total_hours < min_hours:
            self.warnings.append(
                f"Total hours ({total_hours:.1f}h) is below goal ({weekly_study_goal}h) by more than 20%"
            )
            return False
        elif total_hours > max_hours:
            self.warnings.append(
                f"Total hours ({total_hours:.1f}h) exceeds goal ({weekly_study_goal}h) by more than 20%"
            )
            return False
        
        return True
    
    def _correct_subject_references(
        self, 
        plan_data: Dict[str, Any], 
        subject_map: Dict[str, Subject]
    ) -> Dict[str, Any]:
        """Attempt to correct invalid subject references"""
        corrected_sessions = []
        
        for i, session in enumerate(plan_data["sessions"]):
            subject_name = session.get("subject_name")
            
            if subject_name in subject_map:
                corrected_sessions.append(session)
            else:
                # Try fuzzy matching (case-insensitive)
                found = False
                for valid_name in subject_map.keys():
                    if valid_name.lower() == subject_name.lower():
                        session["subject_name"] = valid_name
                        corrected_sessions.append(session)
                        self.corrections_made.append(
                            f"Session {i}: Corrected subject name '{subject_name}' to '{valid_name}'"
                        )
                        found = True
                        break
                
                if not found:
                    # Remove this session
                    self.corrections_made.append(
                        f"Session {i}: Removed session with invalid subject '{subject_name}'"
                    )
        
        plan_data["sessions"] = corrected_sessions
        return plan_data
    
    def _correct_session_times(
        self, 
        plan_data: Dict[str, Any], 
        valid_slots: List[TimeSlot]
    ) -> Dict[str, Any]:
        """Attempt to adjust session times to fit valid slots"""
        slots_by_day = {}
        for slot in valid_slots:
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = []
            slots_by_day[slot.day].append(slot)
        
        corrected_sessions = []
        
        for i, session in enumerate(plan_data["sessions"]):
            day = session.get("day")
            
            if day not in slots_by_day:
                self.corrections_made.append(
                    f"Session {i}: Removed session on {day} (no valid slots)"
                )
                continue
            
            try:
                start_time = datetime.strptime(session.get("start_time"), "%H:%M:%S").time()
                end_time = datetime.strptime(session.get("end_time"), "%H:%M:%S").time()
            except (ValueError, TypeError):
                self.corrections_made.append(
                    f"Session {i}: Removed session with invalid time format"
                )
                continue
            
            # Check if already in valid slot
            in_valid_slot = False
            for slot in slots_by_day[day]:
                if start_time >= slot.start_time and end_time <= slot.end_time:
                    in_valid_slot = True
                    break
            
            if in_valid_slot:
                corrected_sessions.append(session)
            else:
                # Try to fit in first available slot
                duration = (
                    datetime.combine(datetime.today(), end_time) - 
                    datetime.combine(datetime.today(), start_time)
                ).total_seconds() / 60
                
                fitted = False
                for slot in slots_by_day[day]:
                    if slot.duration_minutes >= duration:
                        session["start_time"] = slot.start_time.strftime("%H:%M:%S")
                        new_end = (
                            datetime.combine(datetime.today(), slot.start_time) + 
                            timedelta(minutes=duration)
                        ).time()
                        session["end_time"] = new_end.strftime("%H:%M:%S")
                        corrected_sessions.append(session)
                        self.corrections_made.append(
                            f"Session {i}: Adjusted time to fit in valid slot"
                        )
                        fitted = True
                        break
                
                if not fitted:
                    self.corrections_made.append(
                        f"Session {i}: Removed session (couldn't fit in valid slots)"
                    )
        
        plan_data["sessions"] = corrected_sessions
        return plan_data
    
    def _correct_constraint_violations(
        self, 
        plan_data: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Attempt to fix constraint violations"""
        # For now, just remove sessions that violate max_daily_hours
        if constraints.get("max_daily_hours"):
            max_hours = constraints["max_daily_hours"]
            
            # Group sessions by day
            sessions_by_day = {}
            for session in plan_data["sessions"]:
                day = session.get("day")
                if day not in sessions_by_day:
                    sessions_by_day[day] = []
                sessions_by_day[day].append(session)
            
            corrected_sessions = []
            
            for day, day_sessions in sessions_by_day.items():
                daily_total = 0
                for session in day_sessions:
                    start_time = datetime.strptime(session.get("start_time"), "%H:%M:%S").time()
                    end_time = datetime.strptime(session.get("end_time"), "%H:%M:%S").time()
                    
                    duration_hours = (
                        datetime.combine(datetime.today(), end_time) - 
                        datetime.combine(datetime.today(), start_time)
                    ).total_seconds() / 3600
                    
                    if daily_total + duration_hours <= max_hours:
                        corrected_sessions.append(session)
                        daily_total += duration_hours
                    else:
                        self.corrections_made.append(
                            f"Removed session on {day} to respect max_daily_hours constraint"
                        )
            
            plan_data["sessions"] = corrected_sessions
        
        return plan_data
    
    def _remove_invalid_sessions(
        self, 
        plan_data: Dict[str, Any], 
        valid_slots: List[TimeSlot],
        subject_map: Dict[str, Subject]
    ) -> Dict[str, Any]:
        """Remove any remaining invalid sessions"""
        from datetime import timedelta
        
        slots_by_day = {}
        for slot in valid_slots:
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = []
            slots_by_day[slot.day].append(slot)
        
        valid_sessions = []
        
        for session in plan_data["sessions"]:
            # Check subject
            if session.get("subject_name") not in subject_map:
                continue
            
            # Check day
            day = session.get("day")
            if day not in slots_by_day:
                continue
            
            # Check time
            try:
                start_time = datetime.strptime(session.get("start_time"), "%H:%M:%S").time()
                end_time = datetime.strptime(session.get("end_time"), "%H:%M:%S").time()
                
                # Check if in valid slot
                in_valid_slot = False
                for slot in slots_by_day[day]:
                    if start_time >= slot.start_time and end_time <= slot.end_time:
                        in_valid_slot = True
                        break
                
                if in_valid_slot:
                    valid_sessions.append(session)
            except (ValueError, TypeError):
                continue
        
        plan_data["sessions"] = valid_sessions
        
        # Recalculate total hours
        total_hours = 0
        for session in valid_sessions:
            start_time = datetime.strptime(session.get("start_time"), "%H:%M:%S").time()
            end_time = datetime.strptime(session.get("end_time"), "%H:%M:%S").time()
            duration_hours = (
                datetime.combine(datetime.today(), end_time) - 
                datetime.combine(datetime.today(), start_time)
            ).total_seconds() / 3600
            total_hours += duration_hours
        
        plan_data["total_hours"] = round(total_hours, 2)
        
        return plan_data
    
    def _build_error_response(self) -> Dict[str, Any]:
        """Build error response"""
        return {
            "valid": False,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings
        }
