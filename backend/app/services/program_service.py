"""
Study Program Service for managing study programs (Filières)

Provides CRUD operations, university linking logic, dependent entity counting,
pagination, and filtering support.

Requirements: 2.1-2.7 (Study Program Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from datetime import datetime, timezone

from app.models.study_program import StudyProgram, university_programs
from app.models.university import University
from app.models.academic_track import AcademicTrack
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course


class ProgramService:
    """Service for study program management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_program(self, program_data: Dict[str, Any]) -> StudyProgram:
        """
        Create new study program with validation.
        
        Requirements: 2.1, 2.5
        
        Args:
            program_data: Dictionary with program fields (name, name_de, description, code, etc.)
            
        Returns:
            Created StudyProgram instance
            
        Raises:
            ValueError: If program code already exists
        """
        # Validate unique code if provided
        if program_data.get("code"):
            existing = self.db.query(StudyProgram).filter(
                StudyProgram.code == program_data.get("code"),
                StudyProgram.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Study program with code '{program_data.get('code')}' already exists")
        
        # Create program
        program = StudyProgram(**program_data)
        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)
        
        return program
    
    async def get_programs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[StudyProgram], int]:
        """
        Get paginated list of study programs with optional filters.
        
        Requirements: 2.7
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - university_id: Filter by linked university
                - ids: List of program IDs to filter
                
        Returns:
            Tuple of (list of programs, total count)
        """
        query = self.db.query(StudyProgram).filter(StudyProgram.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        StudyProgram.name.ilike(search_term),
                        StudyProgram.name_de.ilike(search_term),
                        StudyProgram.description.ilike(search_term),
                        StudyProgram.description_de.ilike(search_term),
                        StudyProgram.code.ilike(search_term)
                    )
                )
            
            if filters.get("university_id"):
                # Filter by university through the association table
                query = query.join(university_programs).filter(
                    university_programs.c.university_id == filters["university_id"]
                )
            
            if filters.get("ids"):
                query = query.filter(StudyProgram.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        programs = query.order_by(StudyProgram.name).offset(skip).limit(limit).all()
        
        return programs, total_count
    
    async def get_program_by_id(self, program_id: int) -> Optional[StudyProgram]:
        """
        Get study program by ID.
        
        Args:
            program_id: ID of the study program
            
        Returns:
            StudyProgram instance or None if not found
        """
        return self.db.query(StudyProgram).filter(
            StudyProgram.id == program_id,
            StudyProgram.is_deleted == False
        ).first()
    
    async def update_program(
        self, 
        program_id: int, 
        program_data: Dict[str, Any]
    ) -> StudyProgram:
        """
        Update study program information.
        
        Requirements: 2.3
        
        Args:
            program_id: ID of the program to update
            program_data: Dictionary with fields to update
            
        Returns:
            Updated StudyProgram instance
            
        Raises:
            ValueError: If program not found or code conflict
        """
        program = await self.get_program_by_id(program_id)
        
        if not program:
            raise ValueError(f"Study program with ID {program_id} not found")
        
        # Check for code uniqueness if code is being updated
        if "code" in program_data and program_data["code"] != program.code:
            existing = self.db.query(StudyProgram).filter(
                StudyProgram.code == program_data["code"],
                StudyProgram.id != program_id,
                StudyProgram.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Study program with code '{program_data['code']}' already exists")
        
        # Update fields
        for key, value in program_data.items():
            if hasattr(program, key):
                setattr(program, key, value)
        
        program.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(program)
        
        return program
    
    async def delete_program(self, program_id: int) -> Dict[str, Any]:
        """
        Soft delete study program and return dependent entity counts.
        
        Requirements: 2.4
        
        Args:
            program_id: ID of the program to delete
            
        Returns:
            Dictionary with deletion result and dependent entity counts
            
        Raises:
            ValueError: If program not found
        """
        program = await self.get_program_by_id(program_id)
        
        if not program:
            raise ValueError(f"Study program with ID {program_id} not found")
        
        # Get dependent entity counts
        dependent_counts = await self.get_dependent_counts(program_id)
        
        # Perform soft delete
        program.is_deleted = True
        program.deleted_at = datetime.now(timezone.utc)
        
        # Also soft delete academic tracks
        for track in program.academic_tracks:
            if not track.is_deleted:
                track.is_deleted = True
                track.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Study program '{program.name}' has been deleted",
            "dependent_counts": dependent_counts
        }
    
    async def get_dependent_counts(self, program_id: int) -> Dict[str, int]:
        """
        Get counts of entities dependent on this program.
        
        Requirements: 2.4
        
        Args:
            program_id: ID of the study program
            
        Returns:
            Dictionary with counts of dependent entities:
                - universities: Number of linked universities
                - tracks: Number of academic tracks
                - semesters: Number of semesters (through tracks)
                - courses: Number of courses (through semesters)
        """
        # Count linked universities
        universities_count = self.db.query(func.count(university_programs.c.university_id)).filter(
            university_programs.c.study_program_id == program_id
        ).scalar() or 0
        
        # Count academic tracks
        tracks_count = self.db.query(func.count(AcademicTrack.id)).filter(
            AcademicTrack.study_program_id == program_id,
            AcademicTrack.is_deleted == False
        ).scalar() or 0
        
        # Get track IDs
        track_ids = self.db.query(AcademicTrack.id).filter(
            AcademicTrack.study_program_id == program_id,
            AcademicTrack.is_deleted == False
        ).all()
        track_ids = [tid[0] for tid in track_ids]
        
        semesters_count = 0
        courses_count = 0
        
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
            "universities": universities_count,
            "tracks": tracks_count,
            "semesters": semesters_count,
            "courses": courses_count
        }
    
    # University linking methods
    
    async def link_program_to_university(
        self, 
        program_id: int, 
        university_id: int
    ) -> Dict[str, Any]:
        """
        Link study program to a university with validation.
        
        Requirements: 2.2, 2.6
        
        Args:
            program_id: ID of the study program
            university_id: ID of the university
            
        Returns:
            Dictionary with success message
            
        Raises:
            ValueError: If program/university not found or link already exists
        """
        # Validate program exists
        program = await self.get_program_by_id(program_id)
        if not program:
            raise ValueError(f"Study program with ID {program_id} not found")
        
        # Validate university exists
        university = self.db.query(University).filter(
            University.id == university_id,
            University.is_deleted == False
        ).first()
        if not university:
            raise ValueError(f"University with ID {university_id} not found")
        
        # Check if link already exists
        existing_link = self.db.query(university_programs).filter(
            and_(
                university_programs.c.study_program_id == program_id,
                university_programs.c.university_id == university_id
            )
        ).first()
        
        if existing_link:
            raise ValueError(
                f"Study program '{program.name}' is already linked to university '{university.name}'"
            )
        
        # Create link
        stmt = university_programs.insert().values(
            study_program_id=program_id,
            university_id=university_id,
            created_at=datetime.now(timezone.utc)
        )
        self.db.execute(stmt)
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Study program '{program.name}' has been linked to university '{university.name}'"
        }
    
    async def unlink_program_from_university(
        self, 
        program_id: int, 
        university_id: int
    ) -> Dict[str, Any]:
        """
        Unlink study program from a university.
        
        Requirements: 2.2
        
        Args:
            program_id: ID of the study program
            university_id: ID of the university
            
        Returns:
            Dictionary with success message
            
        Raises:
            ValueError: If link not found
        """
        # Check if link exists
        existing_link = self.db.query(university_programs).filter(
            and_(
                university_programs.c.study_program_id == program_id,
                university_programs.c.university_id == university_id
            )
        ).first()
        
        if not existing_link:
            raise ValueError(
                f"No link found between program ID {program_id} and university ID {university_id}"
            )
        
        # Delete link
        stmt = university_programs.delete().where(
            and_(
                university_programs.c.study_program_id == program_id,
                university_programs.c.university_id == university_id
            )
        )
        self.db.execute(stmt)
        self.db.commit()
        
        return {
            "success": True,
            "message": "Study program has been unlinked from university"
        }
    
    async def get_programs_by_university(
        self, 
        university_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[StudyProgram], int]:
        """
        Get all study programs linked to a specific university.
        
        Requirements: 2.7
        
        Args:
            university_id: ID of the university
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of programs, total count)
        """
        query = self.db.query(StudyProgram).join(university_programs).filter(
            university_programs.c.university_id == university_id,
            StudyProgram.is_deleted == False
        )
        
        total_count = query.count()
        programs = query.order_by(StudyProgram.name).offset(skip).limit(limit).all()
        
        return programs, total_count
    
    async def get_universities_by_program(
        self, 
        program_id: int
    ) -> List[University]:
        """
        Get all universities linked to a specific program.
        
        Requirements: 2.7
        
        Args:
            program_id: ID of the study program
            
        Returns:
            List of universities
        """
        universities = self.db.query(University).join(university_programs).filter(
            university_programs.c.study_program_id == program_id,
            University.is_deleted == False
        ).order_by(University.name).all()
        
        return universities
