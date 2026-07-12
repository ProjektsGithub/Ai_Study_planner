"""
Teaching Unit Service for managing teaching units within semesters

Provides CRUD operations for teaching units (UE - Unité d'Enseignement).
Handles linking to semesters, ECTS validation, and dependent entity counting.

Requirements: 5.1-5.7 (Teaching Unit Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone

from app.models.teaching_unit import TeachingUnit
from app.models.semester import Semester
from app.models.course import Course


class TeachingUnitService:
    """Service for teaching unit management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_teaching_unit(self, teaching_unit_data: Dict[str, Any]) -> TeachingUnit:
        """
        Create new teaching unit with validation.
        
        Requirements: 5.1, 5.2, 5.5, 5.7
        
        Args:
            teaching_unit_data: Dictionary with teaching unit fields (semester_id, name, etc.)
            
        Returns:
            Created TeachingUnit instance
            
        Raises:
            ValueError: If semester not found or validation fails
        """
        # Requirement 5.7: Validate semester exists
        semester_id = teaching_unit_data.get("semester_id")
        semester = self.db.query(Semester).filter(
            Semester.id == semester_id,
            Semester.is_deleted == False
        ).first()
        
        if not semester:
            raise ValueError(f"Semester with ID {semester_id} not found")
        
        # Requirement 5.5: Validate ECTS if provided
        ects_required = teaching_unit_data.get("ects_required")
        if ects_required is not None and ects_required < 0:
            raise ValueError("ECTS required must be a non-negative integer")
        
        # Validate code uniqueness if provided
        code = teaching_unit_data.get("code")
        if code:
            existing_unit = self.db.query(TeachingUnit).filter(
                TeachingUnit.code == code,
                TeachingUnit.is_deleted == False
            ).first()
            
            if existing_unit:
                raise ValueError(f"Teaching unit with code '{code}' already exists")
        
        # Create teaching unit
        teaching_unit = TeachingUnit(**teaching_unit_data)
        self.db.add(teaching_unit)
        self.db.commit()
        self.db.refresh(teaching_unit)
        
        return teaching_unit
    
    async def get_teaching_units(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[TeachingUnit], int]:
        """
        Get paginated list of teaching units with optional filters.
        
        Requirements: 5.6
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - semester_id: Filter by semester
                - academic_track_id: Filter by academic track (via semester)
                - ids: List of teaching unit IDs to filter
                
        Returns:
            Tuple of (list of teaching units, total count)
        """
        query = self.db.query(TeachingUnit).filter(TeachingUnit.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        TeachingUnit.name.ilike(search_term),
                        TeachingUnit.name_de.ilike(search_term),
                        TeachingUnit.code.ilike(search_term),
                        TeachingUnit.description.ilike(search_term),
                        TeachingUnit.description_de.ilike(search_term)
                    )
                )
            
            if filters.get("semester_id"):
                query = query.filter(TeachingUnit.semester_id == filters["semester_id"])
            
            if filters.get("academic_track_id"):
                # Join with Semester to filter by academic track
                query = query.join(Semester).filter(
                    Semester.academic_track_id == filters["academic_track_id"]
                )
            
            if filters.get("ids"):
                query = query.filter(TeachingUnit.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination - order by semester_id and name
        teaching_units = query.order_by(
            TeachingUnit.semester_id, 
            TeachingUnit.name
        ).offset(skip).limit(limit).all()
        
        return teaching_units, total_count
    
    async def get_teaching_unit_by_id(self, teaching_unit_id: int) -> Optional[TeachingUnit]:
        """
        Get teaching unit by ID.
        
        Args:
            teaching_unit_id: ID of the teaching unit
            
        Returns:
            TeachingUnit instance or None if not found
        """
        return self.db.query(TeachingUnit).filter(
            TeachingUnit.id == teaching_unit_id,
            TeachingUnit.is_deleted == False
        ).first()
    
    async def update_teaching_unit(
        self, 
        teaching_unit_id: int, 
        teaching_unit_data: Dict[str, Any]
    ) -> TeachingUnit:
        """
        Update teaching unit information.
        
        Requirements: 5.3
        
        Args:
            teaching_unit_id: ID of the teaching unit to update
            teaching_unit_data: Dictionary with fields to update
            
        Returns:
            Updated TeachingUnit instance
            
        Raises:
            ValueError: If teaching unit not found or validation fails
        """
        teaching_unit = await self.get_teaching_unit_by_id(teaching_unit_id)
        
        if not teaching_unit:
            raise ValueError(f"Teaching unit with ID {teaching_unit_id} not found")
        
        # Validate semester exists if being updated
        if "semester_id" in teaching_unit_data:
            semester = self.db.query(Semester).filter(
                Semester.id == teaching_unit_data["semester_id"],
                Semester.is_deleted == False
            ).first()
            
            if not semester:
                raise ValueError(f"Semester with ID {teaching_unit_data['semester_id']} not found")
        
        # Validate ECTS if being updated
        if "ects_required" in teaching_unit_data:
            ects_required = teaching_unit_data["ects_required"]
            if ects_required is not None and ects_required < 0:
                raise ValueError("ECTS required must be a non-negative integer")
        
        # Validate code uniqueness if being updated
        if "code" in teaching_unit_data:
            code = teaching_unit_data["code"]
            if code:
                existing_unit = self.db.query(TeachingUnit).filter(
                    TeachingUnit.code == code,
                    TeachingUnit.id != teaching_unit_id,
                    TeachingUnit.is_deleted == False
                ).first()
                
                if existing_unit:
                    raise ValueError(f"Teaching unit with code '{code}' already exists")
        
        # Update fields
        for key, value in teaching_unit_data.items():
            if hasattr(teaching_unit, key):
                setattr(teaching_unit, key, value)
        
        teaching_unit.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(teaching_unit)
        
        return teaching_unit
    
    async def delete_teaching_unit(self, teaching_unit_id: int) -> Dict[str, Any]:
        """
        Soft delete teaching unit and return dependent entity counts.
        
        Requirements: 5.4
        
        Args:
            teaching_unit_id: ID of the teaching unit to delete
            
        Returns:
            Dictionary with deletion result and dependent entity counts
            
        Raises:
            ValueError: If teaching unit not found or has courses assigned
        """
        teaching_unit = await self.get_teaching_unit_by_id(teaching_unit_id)
        
        if not teaching_unit:
            raise ValueError(f"Teaching unit with ID {teaching_unit_id} not found")
        
        # Get dependent entity counts
        dependent_counts = await self.get_dependent_counts(teaching_unit_id)
        
        # Requirement 5.4: Prevent deletion if courses are assigned
        if dependent_counts.get("courses", 0) > 0:
            raise ValueError(
                f"Cannot delete teaching unit with {dependent_counts['courses']} assigned courses. "
                f"Please remove or reassign courses before deleting this teaching unit."
            )
        
        # Perform soft delete
        teaching_unit.is_deleted = True
        teaching_unit.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Teaching unit '{teaching_unit.name}' has been deleted",
            "dependent_counts": dependent_counts
        }
    
    async def get_dependent_counts(self, teaching_unit_id: int) -> Dict[str, int]:
        """
        Get counts of entities dependent on this teaching unit.
        
        Args:
            teaching_unit_id: ID of the teaching unit
            
        Returns:
            Dictionary with counts of dependent entities:
                - courses: Number of courses
        """
        # Count courses
        courses_count = self.db.query(func.count(Course.id)).filter(
            Course.teaching_unit_id == teaching_unit_id,
            Course.is_deleted == False
        ).scalar() or 0
        
        return {
            "courses": courses_count
        }
