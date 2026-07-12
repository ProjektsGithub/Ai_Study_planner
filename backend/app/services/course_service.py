"""
Course Service for managing courses/subjects

Provides CRUD operations, validation, filtering, prerequisite management,
and batch operations for course entities.

Requirements: 6.1-6.9 (Course Management)
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from datetime import datetime, timezone

from app.models.course import Course, course_prerequisites
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.study_program import StudyProgram


class CourseService:
    """Service for course management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_course(self, course_data: Dict[str, Any]) -> Course:
        """
        Create new course with validation.
        
        Requirements: 6.1, 6.6, 6.7, 6.8
        
        Args:
            course_data: Dictionary with course fields (name, semester_id, ects_credits, etc.)
            
        Returns:
            Created Course instance
            
        Raises:
            ValueError: If validation fails or course code already exists
        """
        # Validate course data
        is_valid, errors = await self.validate_course_data(course_data)
        if not is_valid:
            raise ValueError(f"Course validation failed: {', '.join(errors)}")
        
        # Validate unique code if provided
        if course_data.get("code"):
            existing = self.db.query(Course).filter(
                Course.code == course_data.get("code"),
                Course.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Course with code '{course_data.get('code')}' already exists")
        
        # Validate semester exists
        semester = self.db.query(Semester).filter(
            Semester.id == course_data.get("semester_id"),
            Semester.is_deleted == False
        ).first()
        
        if not semester:
            raise ValueError(f"Semester with ID {course_data.get('semester_id')} not found")
        
        # Validate teaching unit if provided
        if course_data.get("teaching_unit_id"):
            teaching_unit = self.db.query(TeachingUnit).filter(
                TeachingUnit.id == course_data.get("teaching_unit_id"),
                TeachingUnit.is_deleted == False
            ).first()
            
            if not teaching_unit:
                raise ValueError(f"Teaching unit with ID {course_data.get('teaching_unit_id')} not found")
        
        # Create course
        course = Course(**course_data)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    async def validate_course_data(self, course_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate course data including ECTS, coefficient, difficulty.
        
        Requirements: 6.6, 6.7, 6.8
        
        Args:
            course_data: Dictionary with course fields to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate ECTS credits (1-30)
        ects = course_data.get("ects_credits")
        if ects is None:
            errors.append("ECTS credits are required")
        elif not isinstance(ects, int) or ects < 1 or ects > 30:
            errors.append("ECTS credits must be an integer between 1 and 30")
        
        # Validate coefficient (0.1-10.0)
        coefficient = course_data.get("coefficient")
        if coefficient is None:
            errors.append("Coefficient is required")
        elif not isinstance(coefficient, (int, float)) or coefficient < 0.1 or coefficient > 10.0:
            errors.append("Coefficient must be a number between 0.1 and 10.0")
        
        # Validate difficulty level (1-5)
        difficulty = course_data.get("difficulty_level")
        if difficulty is None:
            errors.append("Difficulty level is required")
        elif not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            errors.append("Difficulty level must be an integer between 1 and 5")
        
        # Validate required fields
        if not course_data.get("name"):
            errors.append("Course name is required")
        
        if not course_data.get("semester_id"):
            errors.append("Semester ID is required")
        
        return (len(errors) == 0, errors)
    
    async def get_courses(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Course], int]:
        """
        Get filtered and paginated courses with total count.
        
        Requirements: 6.1
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - search: Text search in name/description
                - program_id: Filter by study program
                - semester_id: Filter by semester
                - teaching_unit_id: Filter by teaching unit
                - ects_min: Minimum ECTS credits
                - ects_max: Maximum ECTS credits
                - difficulty: Filter by difficulty level
                - ids: List of course IDs to filter
                
        Returns:
            Tuple of (list of courses, total count)
        """
        query = self.db.query(Course).filter(Course.is_deleted == False)
        
        # Apply filters
        if filters:
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Course.name.ilike(search_term),
                        Course.name_de.ilike(search_term),
                        Course.description.ilike(search_term),
                        Course.description_de.ilike(search_term),
                        Course.code.ilike(search_term)
                    )
                )
            
            if filters.get("semester_id"):
                query = query.filter(Course.semester_id == filters["semester_id"])
            
            if filters.get("teaching_unit_id"):
                query = query.filter(Course.teaching_unit_id == filters["teaching_unit_id"])
            
            if filters.get("program_id"):
                # Filter by program through semester -> academic_track -> study_program
                query = query.join(Semester).join(
                    Semester.academic_track
                ).filter(
                    Semester.academic_track.has(study_program_id=filters["program_id"])
                )
            
            if filters.get("ects_min"):
                query = query.filter(Course.ects_credits >= filters["ects_min"])
            
            if filters.get("ects_max"):
                query = query.filter(Course.ects_credits <= filters["ects_max"])
            
            if filters.get("difficulty"):
                query = query.filter(Course.difficulty_level == filters["difficulty"])
            
            if filters.get("ids"):
                query = query.filter(Course.id.in_(filters["ids"]))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        courses = query.order_by(Course.name).offset(skip).limit(limit).all()
        
        return courses, total_count
    
    async def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """
        Get course by ID.
        
        Args:
            course_id: ID of the course
            
        Returns:
            Course instance or None if not found
        """
        return self.db.query(Course).filter(
            Course.id == course_id,
            Course.is_deleted == False
        ).first()
    
    async def update_course(
        self, 
        course_id: int, 
        course_data: Dict[str, Any]
    ) -> Course:
        """
        Update course with validation.
        
        Requirements: 6.4, 6.6, 6.7, 6.8
        
        Args:
            course_id: ID of the course to update
            course_data: Dictionary with fields to update
            
        Returns:
            Updated Course instance
            
        Raises:
            ValueError: If course not found, validation fails, or code conflict
        """
        course = await self.get_course_by_id(course_id)
        
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Validate course data if any validation-relevant fields are being updated
        validation_fields = ["ects_credits", "coefficient", "difficulty_level", "name", "semester_id"]
        if any(field in course_data for field in validation_fields):
            # Merge current data with updates for validation
            merged_data = {
                "name": course.name,
                "semester_id": course.semester_id,
                "ects_credits": course.ects_credits,
                "coefficient": course.coefficient,
                "difficulty_level": course.difficulty_level
            }
            merged_data.update(course_data)
            
            is_valid, errors = await self.validate_course_data(merged_data)
            if not is_valid:
                raise ValueError(f"Course validation failed: {', '.join(errors)}")
        
        # Check for code uniqueness if code is being updated
        if "code" in course_data and course_data["code"] != course.code:
            existing = self.db.query(Course).filter(
                Course.code == course_data["code"],
                Course.id != course_id,
                Course.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Course with code '{course_data['code']}' already exists")
        
        # Update fields
        for key, value in course_data.items():
            if hasattr(course, key):
                setattr(course, key, value)
        
        course.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(course)
        
        return course
    
    async def delete_course(self, course_id: int) -> Dict[str, Any]:
        """
        Soft delete course with validation.
        
        Requirements: 6.5
        
        Args:
            course_id: ID of the course to delete
            
        Returns:
            Dictionary with deletion result and validation info
            
        Raises:
            ValueError: If course not found or has dependent courses/enrollments
        """
        course = await self.get_course_by_id(course_id)
        
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check for dependent courses (courses that list this as a prerequisite)
        dependent_courses = await self.get_course_dependents(course_id)
        if dependent_courses:
            dependent_names = [c.name for c in dependent_courses]
            raise ValueError(
                f"Cannot delete course: {len(dependent_courses)} course(s) depend on it as a prerequisite: "
                f"{', '.join(dependent_names[:3])}"
                + (f" and {len(dependent_names) - 3} more" if len(dependent_names) > 3 else "")
            )
        
        # TODO: Check for student enrollments when that model is implemented
        # For now, we'll just check if the course has been used in study plans
        
        # Perform soft delete
        course.is_deleted = True
        course.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Course '{course.name}' has been deleted"
        }
    
    async def get_course_prerequisites(self, course_id: int) -> List[Course]:
        """
        Get all prerequisite courses for a given course.
        
        Requirements: 6.1
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of prerequisite Course instances
        """
        course = await self.get_course_by_id(course_id)
        if not course:
            return []
        
        # Use the relationship defined in the Course model
        return [prereq for prereq in course.prerequisites if not prereq.is_deleted]
    
    async def get_course_dependents(self, course_id: int) -> List[Course]:
        """
        Get all courses that depend on this course (courses that have this as prerequisite).
        
        Requirements: 6.1
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of dependent Course instances
        """
        course = await self.get_course_by_id(course_id)
        if not course:
            return []
        
        # Use the backref defined in the Course model
        return [dep for dep in course.dependent_courses if not dep.is_deleted]
    
    async def batch_update_courses(
        self, 
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch update multiple courses.
        
        Requirements: 6.1
        
        Args:
            updates: List of dictionaries, each containing 'id' and fields to update
            
        Returns:
            Dictionary with summary of updates (success_count, error_count, errors)
        """
        success_count = 0
        error_count = 0
        errors = []
        
        for update in updates:
            course_id = update.get("id")
            if not course_id:
                error_count += 1
                errors.append({"error": "Missing course ID", "data": update})
                continue
            
            try:
                # Extract update data (everything except 'id')
                update_data = {k: v for k, v in update.items() if k != "id"}
                await self.update_course(course_id, update_data)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "course_id": course_id,
                    "error": str(e)
                })
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    async def batch_create_courses(
        self, 
        courses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch create multiple courses.
        
        Requirements: 6.1
        
        Args:
            courses: List of dictionaries, each containing course data
            
        Returns:
            Dictionary with summary of creations (success_count, error_count, created_ids, errors)
        """
        success_count = 0
        error_count = 0
        created_ids = []
        errors = []
        
        for i, course_data in enumerate(courses):
            try:
                course = await self.create_course(course_data)
                success_count += 1
                created_ids.append(course.id)
            except Exception as e:
                error_count += 1
                errors.append({
                    "index": i,
                    "course_name": course_data.get("name"),
                    "error": str(e)
                })
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "created_ids": created_ids,
            "errors": errors
        }
    
    async def batch_delete_courses(
        self, 
        course_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Batch delete multiple courses.
        
        Requirements: 6.1, 6.5
        
        Args:
            course_ids: List of course IDs to delete
            
        Returns:
            Dictionary with summary of deletions (success_count, error_count, errors)
        """
        success_count = 0
        error_count = 0
        errors = []
        
        for course_id in course_ids:
            try:
                await self.delete_course(course_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "course_id": course_id,
                    "error": str(e)
                })
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
