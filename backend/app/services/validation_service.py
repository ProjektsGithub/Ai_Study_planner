"""
Validation Service for AI-generated study plans and Super Admin Platform business rules

Validates plans for:
- JSON schema compliance
- Session validity (in valid slots)
- Constraint violations
- Subject references
- Total hours (goal ± 20% tolerance)

Super Admin Platform validations:
- Prerequisite chain circular dependency detection
- ECTS hierarchy validation (graduation >= year >= semester)
- Semester structure validation for Bachelor (S1-S6) and Master (S1-S4)
- Import data validation with detailed error messages

Attempts automatic corrections when possible.
"""
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from collections import deque

from app.models.subject import Subject
from app.models.course import Course
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.semester import Semester
from app.models.validation_rule import ValidationRule, RuleType
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
        removed_count = 0
        
        for session in plan_data["sessions"]:
            # Check subject
            if session.get("subject_name") not in subject_map:
                removed_count += 1
                self.corrections_made.append(f"Removed session: Invalid subject '{session.get('subject_name')}'")
                continue
            
            # Check day - CRITICAL: Must be in available days
            day = session.get("day")
            if day not in slots_by_day:
                removed_count += 1
                self.corrections_made.append(f"🚨 Removed session on {day}: NO availability on this day (available days: {', '.join(sorted(slots_by_day.keys()))})")
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
                else:
                    removed_count += 1
                    self.corrections_made.append(f"Removed session on {day}: Time {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} not in valid slots")
            except (ValueError, TypeError):
                removed_count += 1
                self.corrections_made.append(f"Removed session: Invalid time format")
                continue
        
        if removed_count > 0:
            print(f"[VALIDATION] Removed {removed_count} invalid sessions from AI plan")
            print(f"[VALIDATION] Available days: {', '.join(sorted(slots_by_day.keys()))}")
            print(f"[VALIDATION] Valid sessions remaining: {len(valid_sessions)}")
        
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
    
    # ========================================================================
    # Super Admin Platform Business Rule Validations
    # ========================================================================
    
    async def validate_prerequisite_chain(
        self, 
        db: Session, 
        course_id: int, 
        prerequisite_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate prerequisite relationship doesn't create circular dependency.
        Uses graph traversal (DFS) to detect cycles.
        
        Requirements: 7.2, 7.7, 7.8
        
        Args:
            db: Database session
            course_id: ID of the course that will have the prerequisite
            prerequisite_id: ID of the prerequisite course to be added
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if no circular dependency
            - (False, error_message) if circular dependency detected with the circular path
        """
        # Check if both courses exist
        course = db.query(Course).filter(
            Course.id == course_id, 
            Course.is_deleted == False
        ).first()
        prerequisite = db.query(Course).filter(
            Course.id == prerequisite_id, 
            Course.is_deleted == False
        ).first()
        
        if not course:
            return False, f"Course with ID {course_id} not found"
        
        if not prerequisite:
            return False, f"Prerequisite course with ID {prerequisite_id} not found"
        
        # Validate that prerequisite course is from an earlier or same semester
        if prerequisite.semester_id != course.semester_id:
            prerequisite_semester = db.query(Semester).filter(
                Semester.id == prerequisite.semester_id
            ).first()
            course_semester = db.query(Semester).filter(
                Semester.id == course.semester_id
            ).first()
            
            if prerequisite_semester and course_semester:
                if prerequisite_semester.semester_number > course_semester.semester_number:
                    return False, (
                        f"Invalid prerequisite: '{prerequisite.name}' (Semester {prerequisite_semester.semester_number}) "
                        f"cannot be a prerequisite for '{course.name}' (Semester {course_semester.semester_number}). "
                        f"Prerequisites must be from earlier or same semester."
                    )
        
        # Build adjacency list of current prerequisite relationships
        adjacency_list: Dict[int, List[int]] = {}
        
        # Get all existing prerequisites (not deleted)
        all_courses = db.query(Course).filter(Course.is_deleted == False).all()
        
        for c in all_courses:
            adjacency_list[c.id] = [p.id for p in c.prerequisites if not p.is_deleted]
        
        # Ensure course_id exists in adjacency list
        if course_id not in adjacency_list:
            adjacency_list[course_id] = []
        
        # Add the proposed new prerequisite relationship
        adjacency_list[course_id].append(prerequisite_id)
        
        # Detect cycle using DFS
        visited: Set[int] = set()
        rec_stack: Set[int] = set()
        path: List[int] = []
        cycle_path: List[int] = []
        
        def dfs(node: int) -> bool:
            """DFS to detect cycle. Returns True if cycle found."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visit all prerequisites of this course
            for neighbor in adjacency_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle detected - build the cycle path
                    cycle_start_idx = path.index(neighbor)
                    cycle_path.extend(path[cycle_start_idx:])
                    cycle_path.append(neighbor)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Start DFS from the course that would have the new prerequisite
        if dfs(course_id):
            # Build human-readable cycle path
            cycle_names = []
            for course_id_in_cycle in cycle_path:
                c = db.query(Course).filter(Course.id == course_id_in_cycle).first()
                if c:
                    cycle_names.append(f"{c.name} (ID: {c.id})")
            
            cycle_str = " -> ".join(cycle_names)
            
            return False, (
                f"Circular dependency detected: {cycle_str}. "
                f"Cannot add '{prerequisite.name}' as a prerequisite for '{course.name}'."
            )
        
        return True, None
    
    async def validate_ects_totals(
        self, 
        db: Session, 
        track_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate ECTS requirements hierarchy:
        graduation ECTS >= year_progression ECTS >= semester_validation ECTS
        
        Requirements: 8.6, 8.7
        
        Args:
            db: Database session
            track_id: ID of the academic track to validate
            
        Returns:
            Tuple of (is_valid, validation_details)
            - is_valid: True if hierarchy is valid
            - validation_details: Dict with ECTS values and any error messages
        """
        # Get academic track
        track = db.query(AcademicTrack).filter(
            AcademicTrack.id == track_id,
            AcademicTrack.is_deleted == False
        ).first()
        
        if not track:
            return False, {
                "error": f"Academic track with ID {track_id} not found",
                "track_name": None,
                "graduation_ects": None,
                "year_progression_ects": None,
                "semester_validation_ects": None
            }
        
        # Get validation rules for this track
        rules = db.query(ValidationRule).filter(
            ValidationRule.academic_track_id == track_id,
            ValidationRule.is_deleted == False
        ).all()
        
        graduation_ects = None
        year_progression_ects = None
        semester_validation_ects = None
        
        for rule in rules:
            if rule.rule_type == RuleType.GRADUATION:
                graduation_ects = rule.minimum_ects
            elif rule.rule_type == RuleType.YEAR_PROGRESSION:
                year_progression_ects = rule.minimum_ects
            elif rule.rule_type == RuleType.SEMESTER_VALIDATION:
                semester_validation_ects = rule.minimum_ects
        
        # If graduation ECTS not set in rules, use track's total_ects_required
        if graduation_ects is None:
            graduation_ects = track.total_ects_required
        
        validation_details = {
            "track_name": track.name,
            "track_level": track.level.value,
            "graduation_ects": graduation_ects,
            "year_progression_ects": year_progression_ects,
            "semester_validation_ects": semester_validation_ects,
            "errors": []
        }
        
        # Validate hierarchy
        is_valid = True
        
        # Check: graduation >= year_progression
        if graduation_ects is not None and year_progression_ects is not None:
            if graduation_ects < year_progression_ects:
                is_valid = False
                validation_details["errors"].append(
                    f"Graduation ECTS ({graduation_ects}) must be >= Year Progression ECTS ({year_progression_ects})"
                )
        
        # Check: year_progression >= semester_validation
        if year_progression_ects is not None and semester_validation_ects is not None:
            if year_progression_ects < semester_validation_ects:
                is_valid = False
                validation_details["errors"].append(
                    f"Year Progression ECTS ({year_progression_ects}) must be >= Semester Validation ECTS ({semester_validation_ects})"
                )
        
        # Check: graduation >= semester_validation (transitive, but check for safety)
        if graduation_ects is not None and semester_validation_ects is not None:
            if graduation_ects < semester_validation_ects:
                is_valid = False
                validation_details["errors"].append(
                    f"Graduation ECTS ({graduation_ects}) must be >= Semester Validation ECTS ({semester_validation_ects})"
                )
        
        return is_valid, validation_details
    
    async def validate_semester_structure(
        self, 
        db: Session, 
        track_id: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate semester numbering and structure for academic track.
        Bachelor: S1-S6 (semester_number 1-6)
        Master: S1-S4 (semester_number 1-4)
        
        Requirements: 4.1, 4.2, 4.5
        
        Args:
            db: Database session
            track_id: ID of the academic track to validate
            
        Returns:
            Tuple of (is_valid, error_messages_list)
        """
        # Get academic track
        track = db.query(AcademicTrack).filter(
            AcademicTrack.id == track_id,
            AcademicTrack.is_deleted == False
        ).first()
        
        if not track:
            return False, [f"Academic track with ID {track_id} not found"]
        
        # Get semesters for this track
        semesters = db.query(Semester).filter(
            Semester.academic_track_id == track_id,
            Semester.is_deleted == False
        ).order_by(Semester.semester_number).all()
        
        errors = []
        
        # Define expected structure based on track level
        if track.level == TrackLevel.BACHELOR:
            expected_max = 6
            expected_semesters = list(range(1, 7))  # [1, 2, 3, 4, 5, 6]
        elif track.level == TrackLevel.MASTER:
            expected_max = 4
            expected_semesters = list(range(1, 5))  # [1, 2, 3, 4]
        elif track.level == TrackLevel.DOCTORATE:
            # Doctorate can have custom structure, no strict validation
            return True, []
        else:
            errors.append(f"Unknown track level: {track.level}")
            return False, errors
        
        # Check if we have any semesters
        if not semesters:
            errors.append(
                f"{track.level.value.capitalize()} track '{track.name}' has no semesters configured. "
                f"Expected semesters 1-{expected_max}."
            )
            return False, errors
        
        # Get actual semester numbers
        actual_semester_numbers = [s.semester_number for s in semesters]
        
        # Check for duplicates
        if len(actual_semester_numbers) != len(set(actual_semester_numbers)):
            duplicates = [num for num in actual_semester_numbers if actual_semester_numbers.count(num) > 1]
            errors.append(
                f"Duplicate semester numbers found in track '{track.name}': {set(duplicates)}"
            )
        
        # Check for out-of-range semester numbers
        for semester in semesters:
            if semester.semester_number < 1 or semester.semester_number > expected_max:
                errors.append(
                    f"Semester '{semester.name}' has invalid semester_number {semester.semester_number}. "
                    f"{track.level.value.capitalize()} tracks must have semester numbers between 1 and {expected_max}."
                )
        
        # Check for missing semesters (warning level - not blocking)
        missing_semesters = [num for num in expected_semesters if num not in actual_semester_numbers]
        if missing_semesters:
            # This is informational, not an error
            errors.append(
                f"Warning: Track '{track.name}' is missing semester numbers: {missing_semesters}. "
                f"Standard {track.level.value.capitalize()} structure includes semesters 1-{expected_max}."
            )
        
        # Check semester numbering is sequential (allow gaps, but no skips)
        sorted_numbers = sorted(actual_semester_numbers)
        if sorted_numbers and sorted_numbers[0] != 1:
            errors.append(
                f"Track '{track.name}' semesters should start at 1, but start at {sorted_numbers[0]}"
            )
        
        is_valid = len([e for e in errors if not e.startswith("Warning:")]) == 0
        
        return is_valid, errors
    
    async def validate_import_data(
        self, 
        import_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate complete import data structure and semantics.
        This performs pre-database validation on parsed Excel import data.
        
        Requirements: 9.2, 9.3, 9.5, 14.1-14.8
        
        Args:
            import_data: Parsed import data dictionary with structure:
                {
                    "universities": [...],
                    "programs": [...],
                    "tracks": [...],
                    "semesters": [...],
                    "teaching_units": [...],
                    "courses": [...],
                    "prerequisites": [...]
                }
                
        Returns:
            Tuple of (is_valid, error_messages_list)
        """
        errors = []
        
        # Validate required top-level keys
        required_keys = ["universities", "programs", "tracks", "semesters", "courses"]
        for key in required_keys:
            if key not in import_data:
                errors.append(f"Missing required key in import data: '{key}'")
        
        if errors:
            return False, errors
        
        # Validate universities
        if not isinstance(import_data["universities"], list):
            errors.append("Field 'universities' must be a list")
        else:
            for i, uni in enumerate(import_data["universities"]):
                if not isinstance(uni, dict):
                    errors.append(f"University at index {i}: must be a dictionary")
                    continue
                
                if not uni.get("name"):
                    errors.append(f"University at index {i}: missing required field 'name'")
                
                if not uni.get("country"):
                    errors.append(f"University at index {i}: missing required field 'country'")
        
        # Validate programs
        if not isinstance(import_data["programs"], list):
            errors.append("Field 'programs' must be a list")
        else:
            for i, program in enumerate(import_data["programs"]):
                if not isinstance(program, dict):
                    errors.append(f"Program at index {i}: must be a dictionary")
                    continue
                
                if not program.get("name"):
                    errors.append(f"Program at index {i}: missing required field 'name'")
        
        # Validate tracks
        if not isinstance(import_data["tracks"], list):
            errors.append("Field 'tracks' must be a list")
        else:
            for i, track in enumerate(import_data["tracks"]):
                if not isinstance(track, dict):
                    errors.append(f"Track at index {i}: must be a dictionary")
                    continue
                
                if not track.get("name"):
                    errors.append(f"Track at index {i}: missing required field 'name'")
                
                if not track.get("level"):
                    errors.append(f"Track at index {i}: missing required field 'level'")
                elif track["level"] not in ["bachelor", "master", "doctorate"]:
                    errors.append(
                        f"Track at index {i}: invalid level '{track['level']}'. "
                        f"Must be one of: bachelor, master, doctorate"
                    )
                
                if "total_ects_required" not in track:
                    errors.append(f"Track at index {i}: missing required field 'total_ects_required'")
                elif not isinstance(track["total_ects_required"], int) or track["total_ects_required"] <= 0:
                    errors.append(
                        f"Track at index {i}: 'total_ects_required' must be a positive integer"
                    )
        
        # Validate semesters
        if not isinstance(import_data["semesters"], list):
            errors.append("Field 'semesters' must be a list")
        else:
            for i, semester in enumerate(import_data["semesters"]):
                if not isinstance(semester, dict):
                    errors.append(f"Semester at index {i}: must be a dictionary")
                    continue
                
                if not semester.get("name"):
                    errors.append(f"Semester at index {i}: missing required field 'name'")
                
                if "semester_number" not in semester:
                    errors.append(f"Semester at index {i}: missing required field 'semester_number'")
                elif not isinstance(semester["semester_number"], int) or semester["semester_number"] < 1:
                    errors.append(
                        f"Semester at index {i}: 'semester_number' must be a positive integer"
                    )
        
        # Validate courses
        if not isinstance(import_data["courses"], list):
            errors.append("Field 'courses' must be a list")
        else:
            for i, course in enumerate(import_data["courses"]):
                if not isinstance(course, dict):
                    errors.append(f"Course at index {i}: must be a dictionary")
                    continue
                
                if not course.get("name"):
                    errors.append(f"Course at index {i}: missing required field 'name'")
                
                # Validate ECTS credits (Requirement 6.6)
                if "ects_credits" not in course:
                    errors.append(f"Course at index {i}: missing required field 'ects_credits'")
                elif not isinstance(course["ects_credits"], int) or course["ects_credits"] < 1 or course["ects_credits"] > 30:
                    errors.append(
                        f"Course at index {i} ('{course.get('name', 'unnamed')}'): "
                        f"'ects_credits' must be an integer between 1 and 30"
                    )
                
                # Validate coefficient (Requirement 6.7)
                if "coefficient" not in course:
                    errors.append(f"Course at index {i}: missing required field 'coefficient'")
                elif not isinstance(course["coefficient"], (int, float)) or course["coefficient"] < 0.1 or course["coefficient"] > 10.0:
                    errors.append(
                        f"Course at index {i} ('{course.get('name', 'unnamed')}'): "
                        f"'coefficient' must be a number between 0.1 and 10.0"
                    )
                
                # Validate difficulty level (Requirement 6.8)
                if "difficulty_level" not in course:
                    errors.append(f"Course at index {i}: missing required field 'difficulty_level'")
                elif not isinstance(course["difficulty_level"], int) or course["difficulty_level"] < 1 or course["difficulty_level"] > 5:
                    errors.append(
                        f"Course at index {i} ('{course.get('name', 'unnamed')}'): "
                        f"'difficulty_level' must be an integer between 1 and 5"
                    )
        
        # Validate prerequisites (if present)
        if "prerequisites" in import_data:
            if not isinstance(import_data["prerequisites"], list):
                errors.append("Field 'prerequisites' must be a list")
            else:
                for i, prereq in enumerate(import_data["prerequisites"]):
                    if not isinstance(prereq, dict):
                        errors.append(f"Prerequisite at index {i}: must be a dictionary")
                        continue
                    
                    if "course_id" not in prereq and "course_name" not in prereq:
                        errors.append(
                            f"Prerequisite at index {i}: must have either 'course_id' or 'course_name'"
                        )
                    
                    if "prerequisite_id" not in prereq and "prerequisite_name" not in prereq:
                        errors.append(
                            f"Prerequisite at index {i}: must have either 'prerequisite_id' or 'prerequisite_name'"
                        )
        
        is_valid = len(errors) == 0
        
        return is_valid, errors
