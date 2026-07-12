"""
Academic Track Service for managing academic tracks (Cursus)

Provides CRUD operations for academic tracks including Bachelor, Master, and Doctorate levels.
Handles ECTS validation, linking to study programs, and dependent entity counting.

Requirements: 3.1-3.7 (Academic Track Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone

from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.study_program import StudyProgram
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course


class AcademicTrackService:
    """Service for academic track management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_track(self, track_data: Dict[str, Any]) -> AcademicTrack:
        """
        Create new academic track with validation.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7
        
        Args:
            track_data: Dictionary with track fields (study_program_id, name, level, total_ects_required, etc.)
            
        Returns:
            Created AcademicTrack instance
            
        Raises:
            ValueError: If study program not found or ECTS validation fails
        """
        # Requirement 3.7: Validate study program exists (track must be linked to at least one program)
        study_program_id = track_data.get("study_program_id")
        study_program = self.db.query(StudyProgram).filter(
            StudyProgram.id == study_program_id,
            StudyProgram.is_deleted == False
        ).first()
        
        if not study_program:
            raise ValueError(f"Study program with ID {study_program_id} not found")
        
        # Requirement 3.6: Validate ECTS requirements are positive integers
        total_ects = track_data.get("total_ects_required")
        if total_ects is None or total_ects <= 0:
            raise ValueError("Total ECTS required must be a positive integer")
        
        # Create track
        track = AcademicTrack(**track_data)
        self.db.add(track)
        self.db.commit()
        self.db.refresh(track)
        
        return track
    
    async def get_tracks(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[AcademicTrack], int]:
        """
        Get paginated list of academic tracks with optional filters.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - study_program_id: Filter by study program
                - level: Filter by academic level (bachelor, master, doctorate)
                - ids: List of track IDs to filter
                
        Returns:
            Tuple of (list of tracks, total count)
        """
        query = self.db.query(AcademicTrack).filter(AcademicTrack.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        AcademicTrack.name.ilike(search_term),
                        AcademicTrack.name_de.ilike(search_term),
                        AcademicTrack.description.ilike(search_term),
                        AcademicTrack.description_de.ilike(search_term)
                    )
                )
            
            if filters.get("study_program_id"):
                query = query.filter(AcademicTrack.study_program_id == filters["study_program_id"])
            
            if filters.get("level"):
                query = query.filter(AcademicTrack.level == filters["level"])
            
            if filters.get("ids"):
                query = query.filter(AcademicTrack.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        tracks = query.order_by(AcademicTrack.name).offset(skip).limit(limit).all()
        
        return tracks, total_count
    
    async def get_track_by_id(self, track_id: int) -> Optional[AcademicTrack]:
        """
        Get academic track by ID.
        
        Args:
            track_id: ID of the academic track
            
        Returns:
            AcademicTrack instance or None if not found
        """
        return self.db.query(AcademicTrack).filter(
            AcademicTrack.id == track_id,
            AcademicTrack.is_deleted == False
        ).first()
    
    async def update_track(
        self, 
        track_id: int, 
        track_data: Dict[str, Any]
    ) -> AcademicTrack:
        """
        Update academic track information.
        
        Requirements: 3.5, 3.6
        
        Args:
            track_id: ID of the track to update
            track_data: Dictionary with fields to update
            
        Returns:
            Updated AcademicTrack instance
            
        Raises:
            ValueError: If track not found or validation fails
        """
        track = await self.get_track_by_id(track_id)
        
        if not track:
            raise ValueError(f"Academic track with ID {track_id} not found")
        
        # Requirement 3.6: Validate ECTS if being updated
        if "total_ects_required" in track_data:
            if track_data["total_ects_required"] is None or track_data["total_ects_required"] <= 0:
                raise ValueError("Total ECTS required must be a positive integer")
        
        # Validate study program exists if being updated
        if "study_program_id" in track_data:
            study_program = self.db.query(StudyProgram).filter(
                StudyProgram.id == track_data["study_program_id"],
                StudyProgram.is_deleted == False
            ).first()
            
            if not study_program:
                raise ValueError(f"Study program with ID {track_data['study_program_id']} not found")
        
        # Update fields
        for key, value in track_data.items():
            if hasattr(track, key):
                setattr(track, key, value)
        
        track.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(track)
        
        return track
    
    async def delete_track(self, track_id: int) -> Dict[str, Any]:
        """
        Soft delete academic track and return dependent entity counts.
        
        Args:
            track_id: ID of the track to delete
            
        Returns:
            Dictionary with deletion result and dependent entity counts
            
        Raises:
            ValueError: If track not found
        """
        track = await self.get_track_by_id(track_id)
        
        if not track:
            raise ValueError(f"Academic track with ID {track_id} not found")
        
        # Get dependent entity counts
        dependent_counts = await self.get_dependent_counts(track_id)
        
        # Perform soft delete
        track.is_deleted = True
        track.deleted_at = datetime.now(timezone.utc)
        
        # Also soft delete semesters
        for semester in track.semesters:
            if not semester.is_deleted:
                semester.is_deleted = True
                semester.deleted_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Academic track '{track.name}' has been deleted",
            "dependent_counts": dependent_counts
        }
    
    async def get_dependent_counts(self, track_id: int) -> Dict[str, int]:
        """
        Get counts of entities dependent on this academic track.
        
        Args:
            track_id: ID of the academic track
            
        Returns:
            Dictionary with counts of dependent entities:
                - semesters: Number of semesters
                - teaching_units: Number of teaching units (through semesters)
                - courses: Number of courses (through semesters)
        """
        # Count semesters
        semesters_count = self.db.query(func.count(Semester.id)).filter(
            Semester.academic_track_id == track_id,
            Semester.is_deleted == False
        ).scalar() or 0
        
        # Get semester IDs
        semester_ids = self.db.query(Semester.id).filter(
            Semester.academic_track_id == track_id,
            Semester.is_deleted == False
        ).all()
        semester_ids = [sid[0] for sid in semester_ids]
        
        teaching_units_count = 0
        courses_count = 0
        
        if semester_ids:
            # Count teaching units in these semesters
            teaching_units_count = self.db.query(func.count(TeachingUnit.id)).filter(
                TeachingUnit.semester_id.in_(semester_ids),
                TeachingUnit.is_deleted == False
            ).scalar() or 0
            
            # Count courses in these semesters
            courses_count = self.db.query(func.count(Course.id)).filter(
                Course.semester_id.in_(semester_ids),
                Course.is_deleted == False
            ).scalar() or 0
        
        return {
            "semesters": semesters_count,
            "teaching_units": teaching_units_count,
            "courses": courses_count
        }
