"""
Semester Service for managing semesters within academic tracks

Provides CRUD operations for semesters including S1-S6 for Bachelor and S1-S4 for Master.
Handles semester structure validation, linking to academic tracks, and dependent entity counting.

Requirements: 4.1-4.7 (Semester Configuration Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone

from app.models.semester import Semester
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course


class SemesterService:
    """Service for semester management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_semester(self, semester_data: Dict[str, Any]) -> Semester:
        """
        Create new semester with validation.
        
        Requirements: 4.1, 4.2, 4.3, 4.5, 4.6
        
        Args:
            semester_data: Dictionary with semester fields (academic_track_id, name, semester_number, etc.)
            
        Returns:
            Created Semester instance
            
        Raises:
            ValueError: If academic track not found or validation fails
        """
        # Requirement 4.3: Validate academic track exists
        academic_track_id = semester_data.get("academic_track_id")
        academic_track = self.db.query(AcademicTrack).filter(
            AcademicTrack.id == academic_track_id,
            AcademicTrack.is_deleted == False
        ).first()
        
        if not academic_track:
            raise ValueError(f"Academic track with ID {academic_track_id} not found")
        
        # Validate semester structure based on track level
        semester_number = semester_data.get("semester_number")
        validation_result = await self.validate_semester_structure(
            academic_track_id, 
            semester_number,
            academic_track.level
        )
        
        if not validation_result[0]:
            raise ValueError(validation_result[1])
        
        # Requirement 4.5: Validate semester identifier is unique within academic track
        existing_semester = self.db.query(Semester).filter(
            Semester.academic_track_id == academic_track_id,
            Semester.semester_number == semester_number,
            Semester.is_deleted == False
        ).first()
        
        if existing_semester:
            raise ValueError(f"Semester with number {semester_number} already exists for this academic track")
        
        # Requirement 4.6: Validate ECTS if provided
        ects_required = semester_data.get("ects_required")
        if ects_required is not None and ects_required < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        
        # Create semester
        semester = Semester(**semester_data)
        self.db.add(semester)
        self.db.commit()
        self.db.refresh(semester)
        
        return semester
    
    async def get_semesters(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Semester], int]:
        """
        Get paginated list of semesters with optional filters.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - academic_track_id: Filter by academic track
                - semester_number: Filter by semester number
                - ids: List of semester IDs to filter
                
        Returns:
            Tuple of (list of semesters, total count)
        """
        query = self.db.query(Semester).filter(Semester.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Semester.name.ilike(search_term),
                        Semester.name_de.ilike(search_term),
                        Semester.description.ilike(search_term),
                        Semester.description_de.ilike(search_term)
                    )
                )
            
            if filters.get("academic_track_id"):
                query = query.filter(Semester.academic_track_id == filters["academic_track_id"])
            
            if filters.get("semester_number"):
                query = query.filter(Semester.semester_number == filters["semester_number"])
            
            if filters.get("ids"):
                query = query.filter(Semester.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination - order by academic_track_id and semester_number
        semesters = query.order_by(
            Semester.academic_track_id, 
            Semester.semester_number
        ).offset(skip).limit(limit).all()
        
        return semesters, total_count
    
    async def get_semester_by_id(self, semester_id: int) -> Optional[Semester]:
        """
        Get semester by ID.
        
        Args:
            semester_id: ID of the semester
            
        Returns:
            Semester instance or None if not found
        """
        return self.db.query(Semester).filter(
            Semester.id == semester_id,
            Semester.is_deleted == False
        ).first()
    
    async def update_semester(
        self, 
        semester_id: int, 
        semester_data: Dict[str, Any]
    ) -> Semester:
        """
        Update semester information.
        
        Requirements: 4.5
        
        Args:
            semester_id: ID of the semester to update
            semester_data: Dictionary with fields to update
            
        Returns:
            Updated Semester instance
            
        Raises:
            ValueError: If semester not found or validation fails
        """
        semester = await self.get_semester_by_id(semester_id)
        
        if not semester:
            raise ValueError(f"Semester with ID {semester_id} not found")
        
        # Validate academic track exists if being updated
        if "academic_track_id" in semester_data:
            academic_track = self.db.query(AcademicTrack).filter(
                AcademicTrack.id == semester_data["academic_track_id"],
                AcademicTrack.is_deleted == False
            ).first()
            
            if not academic_track:
                raise ValueError(f"Academic track with ID {semester_data['academic_track_id']} not found")
        
        # Validate semester number if being updated
        if "semester_number" in semester_data:
            semester_number = semester_data["semester_number"]
            academic_track_id = semester_data.get("academic_track_id", semester.academic_track_id)
            
            # Get academic track to check level
            academic_track = self.db.query(AcademicTrack).filter(
                AcademicTrack.id == academic_track_id,
                AcademicTrack.is_deleted == False
            ).first()
            
            if academic_track:
                validation_result = await self.validate_semester_structure(
                    academic_track_id, 
                    semester_number,
                    academic_track.level
                )
                
                if not validation_result[0]:
                    raise ValueError(validation_result[1])
                
                # Check uniqueness (excluding current semester)
                existing_semester = self.db.query(Semester).filter(
                    Semester.academic_track_id == academic_track_id,
                    Semester.semester_number == semester_number,
                    Semester.id != semester_id,
                    Semester.is_deleted == False
                ).first()
                
                if existing_semester:
                    raise ValueError(f"Semester with number {semester_number} already exists for this academic track")
        
        # Validate ECTS if being updated
        if "ects_required" in semester_data:
            ects_required = semester_data["ects_required"]
            if ects_required is not None and ects_required < 0:
                raise ValueError("ECTS required must be a non-negative integer")
        
        # Update fields
        for key, value in semester_data.items():
            if hasattr(semester, key):
                setattr(semester, key, value)
        
        semester.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(semester)
        
        return semester
    
    async def delete_semester(self, semester_id: int) -> Dict[str, Any]:
        """
        Soft delete semester and return dependent entity counts.
        
        Requirements: 4.7
        
        Args:
            semester_id: ID of the semester to delete
            
        Returns:
            Dictionary with deletion result and dependent entity counts
            
        Raises:
            ValueError: If semester not found or has courses assigned
        """
        semester = await self.get_semester_by_id(semester_id)
        
        if not semester:
            raise ValueError(f"Semester with ID {semester_id} not found")
        
        # Get dependent entity counts
        dependent_counts = await self.get_dependent_counts(semester_id)
        
        # Requirement 4.7: Prevent deletion if courses are assigned
        if dependent_counts.get("courses", 0) > 0:
            raise ValueError(
                f"Cannot delete semester with {dependent_counts['courses']} assigned courses. "
                f"Please remove or reassign courses before deleting this semester."
            )
        
        # Perform soft delete
        semester.is_deleted = True
        semester.deleted_at = datetime.now(timezone.utc)
        
        # Also soft delete teaching units
        for teaching_unit in semester.teaching_units:
            if not teaching_unit.is_deleted:
                teaching_unit.is_deleted = True
                teaching_unit.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Semester '{semester.name}' has been deleted",
            "dependent_counts": dependent_counts
        }
    
    async def get_dependent_counts(self, semester_id: int) -> Dict[str, int]:
        """
        Get counts of entities dependent on this semester.
        
        Args:
            semester_id: ID of the semester
            
        Returns:
            Dictionary with counts of dependent entities:
                - teaching_units: Number of teaching units
                - courses: Number of courses
        """
        # Count teaching units
        teaching_units_count = self.db.query(func.count(TeachingUnit.id)).filter(
            TeachingUnit.semester_id == semester_id,
            TeachingUnit.is_deleted == False
        ).scalar() or 0
        
        # Count courses
        courses_count = self.db.query(func.count(Course.id)).filter(
            Course.semester_id == semester_id,
            Course.is_deleted == False
        ).scalar() or 0
        
        return {
            "teaching_units": teaching_units_count,
            "courses": courses_count
        }
    
    async def validate_semester_structure(
        self, 
        academic_track_id: int, 
        semester_number: int,
        track_level: Optional[TrackLevel] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate semester structure based on academic track level.
        
        Requirements: 4.1, 4.2, 4.4
        
        Bachelor tracks: S1-S6 (semester_number 1-6)
        Master tracks: S1-S4 (semester_number 1-4)
        Custom configurations allowed (Requirement 4.4)
        
        Args:
            academic_track_id: ID of the academic track
            semester_number: Semester number to validate
            track_level: Optional track level (if already fetched)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get track level if not provided
        if track_level is None:
            academic_track = self.db.query(AcademicTrack).filter(
                AcademicTrack.id == academic_track_id,
                AcademicTrack.is_deleted == False
            ).first()
            
            if not academic_track:
                return False, f"Academic track with ID {academic_track_id} not found"
            
            track_level = academic_track.level
        
        # Validate semester number range
        if semester_number < 1:
            return False, "Semester number must be at least 1"
        
        # Standard validation for Bachelor and Master
        # Requirement 4.4: Allow custom configurations beyond standard structures
        if track_level == TrackLevel.BACHELOR:
            if semester_number > 6:
                # Warning but allow (custom configuration)
                return True, None  # Allow but note it's non-standard
        elif track_level == TrackLevel.MASTER:
            if semester_number > 4:
                # Warning but allow (custom configuration)
                return True, None  # Allow but note it's non-standard
        # Doctorate has no standard limit (custom)
        
        return True, None
