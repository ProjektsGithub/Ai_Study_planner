"""
Deterministic Planning Engine

This service constructs valid time slots, calculates subject priorities,
and eliminates conflicts before AI generation.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint


class TimeSlot:
    """Represents a time slot for study sessions"""
    
    def __init__(self, day: str, start_time: time, end_time: time):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.duration_minutes = self._calculate_duration()
    
    def _calculate_duration(self) -> int:
        """Calculate duration in minutes"""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another slot on the same day"""
        if self.day != other.day:
            return False
        
        # Check if time ranges overlap
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "day": self.day,
            "start_time": self.start_time.strftime("%H:%M:%S"),
            "end_time": self.end_time.strftime("%H:%M:%S"),
            "duration_minutes": self.duration_minutes
        }
    
    def __repr__(self):
        return f"<TimeSlot({self.day} {self.start_time}-{self.end_time})>"


class SubjectPriority:
    """Represents a subject with calculated priority score"""
    
    def __init__(self, subject: Subject, priority_score: float):
        self.subject = subject
        self.priority_score = priority_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "subject_id": self.subject.id,
            "subject_name": self.subject.name,
            "priority_score": round(self.priority_score, 2),
            "base_priority": self.subject.priority,
            "difficulty": self.subject.difficulty,
            "target_weekly_hours": self.subject.target_weekly_hours,
            "exam_date": self.subject.exam_date.isoformat() if self.subject.exam_date else None
        }
    
    def __repr__(self):
        return f"<SubjectPriority({self.subject.name}: {self.priority_score:.2f})>"


class PlanningEngine:
    """
    Deterministic planning engine that prepares data for AI generation.
    
    Responsibilities:
    1. Construct valid time slots from availabilities and constraints
    2. Calculate subject priorities with weighted scoring
    3. Validate and eliminate conflicts
    """
    
    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.subjects: List[Subject] = []
        self.availabilities: List[Availability] = []
        self.constraints: List[Constraint] = []
        self.valid_slots: List[TimeSlot] = []
        self.subject_priorities: List[SubjectPriority] = []
    
    def load_user_data(self):
        """Load all user data from database"""
        self.subjects = self.db.query(Subject).filter(
            Subject.user_id == self.user_id
        ).all()
        
        self.availabilities = self.db.query(Availability).filter(
            Availability.user_id == self.user_id
        ).all()
        
        self.constraints = self.db.query(Constraint).filter(
            Constraint.user_id == self.user_id,
            Constraint.active == True
        ).all()
    
    def construct_valid_slots(self) -> List[TimeSlot]:
        """
        Construct valid time slots from availabilities and constraints.
        
        Process:
        1. Start with all availability windows
        2. Remove forbidden slot overlaps
        3. Apply fixed slot reservations
        4. Ensure minimum 15-minute slot duration
        
        Returns:
            List of valid TimeSlot objects
        """
        if not self.availabilities:
            raise ValueError("No availabilities defined. Please add availability time slots.")
        
        # Step 1: Convert availabilities to time slots
        slots = []
        for avail in self.availabilities:
            slot = TimeSlot(avail.day_of_week, avail.start_time, avail.end_time)
            if slot.duration_minutes >= 15:  # Minimum 15 minutes
                slots.append(slot)
        
        if not slots:
            raise ValueError("No valid availability slots (minimum 15 minutes required).")
        
        # Step 2: Remove forbidden slots
        forbidden_constraints = [
            c for c in self.constraints 
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
        
        # Step 3: Mark fixed slots (they're still valid but reserved)
        # Fixed slots are handled during AI generation, not here
        
        # Step 4: Filter slots with minimum duration
        valid_slots = [s for s in slots if s.duration_minutes >= 15]
        
        if not valid_slots:
            raise ValueError("No valid time slots after applying constraints.")
        
        self.valid_slots = valid_slots
        return valid_slots
    
    def _remove_forbidden_overlap(
        self, 
        slots: List[TimeSlot], 
        forbidden: TimeSlot
    ) -> List[TimeSlot]:
        """
        Remove forbidden slot overlaps from available slots.
        
        If a slot overlaps with a forbidden slot:
        - If completely overlapped: remove the slot
        - If partially overlapped: split into non-overlapping parts
        """
        result = []
        
        for slot in slots:
            if not slot.overlaps_with(forbidden):
                # No overlap, keep the slot
                result.append(slot)
            else:
                # Overlap detected, split the slot
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
    
    def calculate_priorities(self) -> List[SubjectPriority]:
        """
        Calculate subject priorities with weighted scoring.
        
        Formula (0.0-100.0 scale):
        - Base priority: 20% weight (1-5 scale)
        - Difficulty: 20% weight (1-5 scale)
        - Exam proximity: 40% weight (days until exam)
        - Target hours vs allocated: 20% weight (not implemented yet, will be 0)
        
        Returns:
            List of SubjectPriority objects sorted by score (descending)
        """
        if not self.subjects:
            raise ValueError("No subjects defined. Please add subjects first.")
        
        priorities = []
        
        for subject in self.subjects:
            # Base priority (20% weight): normalize 1-5 to 0-100
            base_score = ((subject.priority - 1) / 4) * 100 * 0.20
            
            # Difficulty (20% weight): normalize 1-5 to 0-100
            difficulty_score = ((subject.difficulty - 1) / 4) * 100 * 0.20
            
            # Exam proximity (40% weight)
            exam_score = self._calculate_exam_proximity_score(subject.exam_date) * 0.40
            
            # Target hours vs allocated (20% weight)
            # Not implemented yet (requires existing plan data)
            # For now, use target_weekly_hours as a factor
            hours_score = min(subject.target_weekly_hours / 20, 1.0) * 100 * 0.20
            
            # Total score
            total_score = base_score + difficulty_score + exam_score + hours_score
            
            priorities.append(SubjectPriority(subject, total_score))
        
        # Sort by priority score (descending)
        priorities.sort(key=lambda x: x.priority_score, reverse=True)
        
        self.subject_priorities = priorities
        return priorities
    
    def _calculate_exam_proximity_score(self, exam_date: date | None) -> float:
        """
        Calculate exam proximity score (0-100).
        
        Logic:
        - No exam date: 50 (neutral)
        - Exam in 0-7 days: 100 (urgent)
        - Exam in 8-30 days: 80-100 (high priority)
        - Exam in 31-60 days: 50-80 (medium priority)
        - Exam in 61+ days: 0-50 (low priority)
        """
        if exam_date is None:
            return 50.0  # Neutral score
        
        days_until_exam = (exam_date - date.today()).days
        
        if days_until_exam < 0:
            # Exam already passed
            return 0.0
        elif days_until_exam <= 7:
            # Very urgent
            return 100.0
        elif days_until_exam <= 30:
            # High priority (linear decay from 100 to 80)
            return 100 - ((days_until_exam - 7) / 23) * 20
        elif days_until_exam <= 60:
            # Medium priority (linear decay from 80 to 50)
            return 80 - ((days_until_exam - 30) / 30) * 30
        else:
            # Low priority (linear decay from 50 to 0)
            return max(0, 50 - ((days_until_exam - 60) / 60) * 50)
    
    def validate_constraints(self) -> Dict[str, Any]:
        """
        Validate constraints and return constraint information.
        
        Returns:
            Dictionary with constraint details for AI generation
        """
        constraint_info = {
            "max_daily_hours": None,
            "required_breaks": [],
            "fixed_slots": [],
            "forbidden_slots_count": 0
        }
        
        for constraint in self.constraints:
            if constraint.constraint_type == "max_daily_hours":
                constraint_info["max_daily_hours"] = constraint.parameters.get("max_hours")
            
            elif constraint.constraint_type == "required_break":
                constraint_info["required_breaks"].append({
                    "duration_minutes": constraint.parameters.get("duration_minutes"),
                    "after_minutes": constraint.parameters.get("after_minutes")
                })
            
            elif constraint.constraint_type == "fixed_slot":
                params = constraint.parameters
                constraint_info["fixed_slots"].append({
                    "day": params.get("day_of_week"),
                    "start_time": params.get("start_time"),
                    "end_time": params.get("end_time"),
                    "subject_id": params.get("subject_id")
                })
            
            elif constraint.constraint_type == "forbidden_slot":
                constraint_info["forbidden_slots_count"] += 1
        
        return constraint_info
    
    def generate_planning_data(self) -> Dict[str, Any]:
        """
        Generate complete planning data for AI generation.
        
        This is the main method that orchestrates all steps:
        1. Load user data
        2. Construct valid slots
        3. Calculate priorities
        4. Validate constraints
        
        Returns:
            Dictionary with all planning data ready for AI
        """
        # Load data
        self.load_user_data()
        
        # Validate we have subjects
        if not self.subjects:
            raise ValueError("No subjects defined. Please add subjects first.")
        
        # Construct valid slots
        valid_slots = self.construct_valid_slots()
        
        # Calculate priorities
        priorities = self.calculate_priorities()
        
        # Validate constraints
        constraint_info = self.validate_constraints()
        
        # Prepare output
        return {
            "valid_slots": [slot.to_dict() for slot in valid_slots],
            "subject_priorities": [p.to_dict() for p in priorities],
            "constraints": constraint_info,
            "total_subjects": len(self.subjects),
            "total_slots": len(valid_slots),
            "total_slot_hours": sum(s.duration_minutes for s in valid_slots) / 60
        }
