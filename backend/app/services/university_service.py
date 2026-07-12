"""
University Service for managing universities and campuses

Provides CRUD operations, dependent entity counting for deletion validation,
pagination, and filtering support.

Requirements: 1.1-1.7 (University Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone

from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram, university_programs
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course


class UniversityService:
    """Service for university management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_university(self, university_data: Dict[str, Any]) -> University:
        """
        Create new university with validation.
        
        Requirements: 1.1, 1.7
        
        Args:
            university_data: Dictionary with university fields (name, name_de, country, description, etc.)
            
        Returns:
            Created University instance
            
        Raises:
            ValueError: If university name already exists
        """
        # Validate unique name
        existing = self.db.query(University).filter(
            University.name == university_data.get("name"),
            University.is_deleted == False
        ).first()
        
        if existing:
            raise ValueError(f"University with name '{university_data.get('name')}' already exists")
        
        # Create university
        university = University(**university_data)
        self.db.add(university)
        self.db.commit()
        self.db.refresh(university)
        
        return university
    
    async def get_universities(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[University], int]:
        """
        Get paginated list of universities with optional filters.
        
        Requirements: 1.4
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - country: Filter by country
                - ids: List of university IDs to filter
                
        Returns:
            Tuple of (list of universities, total count)
        """
        query = self.db.query(University).filter(University.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        University.name.ilike(search_term),
                        University.name_de.ilike(search_term),
                        University.description.ilike(search_term),
                        University.description_de.ilike(search_term)
                    )
                )
            
            if filters.get("country"):
                query = query.filter(University.country == filters["country"])
            
            if filters.get("ids"):
                query = query.filter(University.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        universities = query.order_by(University.name).offset(skip).limit(limit).all()
        
        return universities, total_count
    
    async def get_university_by_id(self, university_id: int) -> Optional[University]:
        """
        Get university by ID.
        
        Args:
            university_id: ID of the university
            
        Returns:
            University instance or None if not found
        """
        return self.db.query(University).filter(
            University.id == university_id,
            University.is_deleted == False
        ).first()
    
    async def update_university(
        self, 
        university_id: int, 
        university_data: Dict[str, Any]
    ) -> University:
        """
        Update university information.
        
        Requirements: 1.2, 1.7
        
        Args:
            university_id: ID of the university to update
            university_data: Dictionary with fields to update
            
        Returns:
            Updated University instance
            
        Raises:
            ValueError: If university not found or name conflict
        """
        university = await self.get_university_by_id(university_id)
        
        if not university:
            raise ValueError(f"University with ID {university_id} not found")
        
        # Check for name uniqueness if name is being updated
        if "name" in university_data and university_data["name"] != university.name:
            existing = self.db.query(University).filter(
                University.name == university_data["name"],
                University.id != university_id,
                University.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"University with name '{university_data['name']}' already exists")
        
        # Update fields
        for key, value in university_data.items():
            if hasattr(university, key):
                setattr(university, key, value)
        
        university.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(university)
        
        return university
    
    async def delete_university(self, university_id: int) -> Dict[str, Any]:
        """
        Soft delete university and return dependent entity counts.
        
        Requirements: 1.3, 1.5
        
        Args:
            university_id: ID of the university to delete
            
        Returns:
            Dictionary with deletion result and dependent entity counts
            
        Raises:
            ValueError: If university not found
        """
        university = await self.get_university_by_id(university_id)
        
        if not university:
            raise ValueError(f"University with ID {university_id} not found")
        
        # Get dependent entity counts
        dependent_counts = await self.get_dependent_counts(university_id)
        
        # Perform soft delete
        university.is_deleted = True
        university.deleted_at = datetime.now(timezone.utc)
        
        # Also soft delete campuses
        for campus in university.campuses:
            if not campus.is_deleted:
                campus.is_deleted = True
                campus.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"University '{university.name}' has been deleted",
            "dependent_counts": dependent_counts
        }
    
    async def get_dependent_counts(self, university_id: int) -> Dict[str, int]:
        """
        Get counts of entities dependent on this university.
        
        Requirements: 1.5
        
        Args:
            university_id: ID of the university
            
        Returns:
            Dictionary with counts of dependent entities:
                - campuses: Number of campuses
                - programs: Number of linked study programs
                - tracks: Number of academic tracks (through programs)
                - semesters: Number of semesters (through tracks)
                - courses: Number of courses (through semesters)
        """
        # Count campuses
        campuses_count = self.db.query(func.count(Campus.id)).filter(
            Campus.university_id == university_id,
            Campus.is_deleted == False
        ).scalar() or 0
        
        # Count linked study programs
        programs_count = self.db.query(func.count(university_programs.c.study_program_id)).filter(
            university_programs.c.university_id == university_id
        ).scalar() or 0
        
        # Get program IDs linked to this university
        program_ids = self.db.query(university_programs.c.study_program_id).filter(
            university_programs.c.university_id == university_id
        ).all()
        program_ids = [pid[0] for pid in program_ids]
        
        tracks_count = 0
        semesters_count = 0
        courses_count = 0
        
        if program_ids:
            # Count academic tracks linked to these programs
            tracks_count = self.db.query(func.count(AcademicTrack.id)).filter(
                AcademicTrack.study_program_id.in_(program_ids),
                AcademicTrack.is_deleted == False
            ).scalar() or 0
            
            # Get track IDs
            track_ids = self.db.query(AcademicTrack.id).filter(
                AcademicTrack.study_program_id.in_(program_ids),
                AcademicTrack.is_deleted == False
            ).all()
            track_ids = [tid[0] for tid in track_ids]
            
            if track_ids:
                # Count semesters in these tracks
                semesters_count = self.db.query(func.count(Semester.id)).filter(
                    Semester.academic_track_id.in_(track_ids),
                    Semester.is_deleted == False
                ).scalar() or 0
                
                # Get semester IDs
                semester_ids = self.db.query(Semester.id).filter(
                    Semester.academic_track_id.in_(track_ids),
                    Semester.is_deleted == False
                ).all()
                semester_ids = [sid[0] for sid in semester_ids]
                
                if semester_ids:
                    # Count courses in these semesters
                    courses_count = self.db.query(func.count(Course.id)).filter(
                        Course.semester_id.in_(semester_ids),
                        Course.is_deleted == False
                    ).scalar() or 0
        
        return {
            "campuses": campuses_count,
            "programs": programs_count,
            "tracks": tracks_count,
            "semesters": semesters_count,
            "courses": courses_count
        }
    
    # Campus management methods
    
    async def create_campus(self, campus_data: Dict[str, Any]) -> Campus:
        """
        Create new campus for a university.
        
        Requirements: 1.6
        
        Args:
            campus_data: Dictionary with campus fields (university_id, name, location, etc.)
            
        Returns:
            Created Campus instance
            
        Raises:
            ValueError: If university not found
        """
        # Validate university exists
        university = await self.get_university_by_id(campus_data.get("university_id"))
        if not university:
            raise ValueError(f"University with ID {campus_data.get('university_id')} not found")
        
        campus = Campus(**campus_data)
        self.db.add(campus)
        self.db.commit()
        self.db.refresh(campus)
        
        return campus
    
    async def get_campuses(
        self, 
        university_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Campus], int]:
        """
        Get paginated list of campuses, optionally filtered by university.
        
        Requirements: 1.6
        
        Args:
            university_id: Optional university ID to filter campuses
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of campuses, total count)
        """
        query = self.db.query(Campus).filter(Campus.is_deleted == False)
        
        if university_id:
            query = query.filter(Campus.university_id == university_id)
        
        total_count = query.count()
        campuses = query.order_by(Campus.name).offset(skip).limit(limit).all()
        
        return campuses, total_count
    
    async def update_campus(self, campus_id: int, campus_data: Dict[str, Any]) -> Campus:
        """
        Update campus information.
        
        Requirements: 1.6
        
        Args:
            campus_id: ID of the campus to update
            campus_data: Dictionary with fields to update
            
        Returns:
            Updated Campus instance
            
        Raises:
            ValueError: If campus not found
        """
        campus = self.db.query(Campus).filter(
            Campus.id == campus_id,
            Campus.is_deleted == False
        ).first()
        
        if not campus:
            raise ValueError(f"Campus with ID {campus_id} not found")
        
        for key, value in campus_data.items():
            if hasattr(campus, key):
                setattr(campus, key, value)
        
        campus.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(campus)
        
        return campus
    
    async def delete_campus(self, campus_id: int) -> Dict[str, Any]:
        """
        Soft delete campus.
        
        Requirements: 1.6
        
        Args:
            campus_id: ID of the campus to delete
            
        Returns:
            Dictionary with deletion result
            
        Raises:
            ValueError: If campus not found
        """
        campus = self.db.query(Campus).filter(
            Campus.id == campus_id,
            Campus.is_deleted == False
        ).first()
        
        if not campus:
            raise ValueError(f"Campus with ID {campus_id} not found")
        
        campus.is_deleted = True
        campus.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Campus '{campus.name}' has been deleted"
        }
