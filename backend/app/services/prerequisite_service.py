"""
Prerequisite Service for managing course prerequisite relationships

Provides operations for creating, deleting, and validating prerequisite relationships,
including circular dependency detection using graph traversal algorithms.

Requirements: 7.1-7.8 (Prerequisite Relationship Management)
"""
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, delete as sql_delete, insert as sql_insert
from datetime import datetime, timezone
from collections import deque

from app.models.course import Course, course_prerequisites


class PrerequisiteService:
    """Service for prerequisite relationship management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_prerequisite(
        self, 
        course_id: int, 
        prerequisite_id: int
    ) -> Dict[str, Any]:
        """
        Create prerequisite relationship with circular dependency validation.
        
        Requirements: 7.1, 7.2, 7.6, 7.7, 7.8
        
        Args:
            course_id: ID of the course that requires the prerequisite
            prerequisite_id: ID of the prerequisite course
            
        Returns:
            Dictionary with created relationship information
            
        Raises:
            ValueError: If validation fails or circular dependency detected
        """
        # Validate both courses exist
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.is_deleted == False
        ).first()
        
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        prerequisite = self.db.query(Course).filter(
            Course.id == prerequisite_id,
            Course.is_deleted == False
        ).first()
        
        if not prerequisite:
            raise ValueError(f"Prerequisite course with ID {prerequisite_id} not found")
        
        # Cannot set a course as its own prerequisite
        if course_id == prerequisite_id:
            raise ValueError("A course cannot be its own prerequisite")
        
        # Check if prerequisite relationship already exists
        existing = self.db.execute(
            course_prerequisites.select().where(
                and_(
                    course_prerequisites.c.course_id == course_id,
                    course_prerequisites.c.prerequisite_id == prerequisite_id
                )
            )
        ).first()
        
        if existing:
            raise ValueError(
                f"Prerequisite relationship already exists between '{course.name}' and '{prerequisite.name}'"
            )
        
        # Validate prerequisite is from earlier or same semester
        if prerequisite.semester.semester_number > course.semester.semester_number:
            raise ValueError(
                f"Prerequisite course '{prerequisite.name}' (Semester {prerequisite.semester.semester_number}) "
                f"cannot be from a later semester than '{course.name}' (Semester {course.semester.semester_number})"
            )
        
        # Validate no circular dependency would be created
        is_valid, error_message = await self.validate_prerequisite(course_id, prerequisite_id)
        if not is_valid:
            raise ValueError(error_message)
        
        # Create prerequisite relationship
        stmt = course_prerequisites.insert().values(
            course_id=course_id,
            prerequisite_id=prerequisite_id,
            created_at=datetime.now(timezone.utc)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        
        return {
            "success": True,
            "course_id": course_id,
            "prerequisite_id": prerequisite_id,
            "message": f"Prerequisite relationship created: '{prerequisite.name}' is now a prerequisite for '{course.name}'"
        }
    
    async def validate_prerequisite(
        self, 
        course_id: int, 
        prerequisite_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate prerequisite relationship before creation (check for cycles).
        
        Requirements: 7.2, 7.8
        
        Args:
            course_id: ID of the course that would require the prerequisite
            prerequisite_id: ID of the proposed prerequisite course
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if adding this prerequisite would create a circular dependency
        # This happens if prerequisite_id already depends (directly or indirectly) on course_id
        has_cycle, cycle_path = await self.detect_circular_dependency(course_id, prerequisite_id)
        
        if has_cycle:
            # Format the cycle path for error message
            cycle_description = " -> ".join([str(cid) for cid in cycle_path])
            course_names = []
            for cid in cycle_path:
                c = self.db.query(Course).filter(Course.id == cid).first()
                if c:
                    course_names.append(c.name)
            
            cycle_names = " -> ".join(course_names)
            
            error_message = (
                f"Circular dependency detected: Adding this prerequisite would create a cycle. "
                f"Cycle path: {cycle_names} (IDs: {cycle_description})"
            )
            return False, error_message
        
        return True, None
    
    async def detect_circular_dependency(
        self, 
        course_id: int, 
        prerequisite_id: int
    ) -> Tuple[bool, Optional[List[int]]]:
        """
        Detect if adding a prerequisite would create a circular dependency.
        Uses Depth-First Search (DFS) to detect cycles.
        
        Requirements: 7.2, 7.8
        
        Args:
            course_id: ID of the course that would require the prerequisite
            prerequisite_id: ID of the proposed prerequisite course
            
        Returns:
            Tuple of (has_cycle, cycle_path if found)
        """
        # Build adjacency list of prerequisite graph
        # For each course, list all its prerequisites
        prerequisites_map = {}
        
        all_prereqs = self.db.execute(
            course_prerequisites.select()
        ).fetchall()
        
        for prereq_rel in all_prereqs:
            if prereq_rel.course_id not in prerequisites_map:
                prerequisites_map[prereq_rel.course_id] = []
            prerequisites_map[prereq_rel.course_id].append(prereq_rel.prerequisite_id)
        
        # Temporarily add the new prerequisite relationship
        if course_id not in prerequisites_map:
            prerequisites_map[course_id] = []
        prerequisites_map[course_id].append(prerequisite_id)
        
        # Check if prerequisite_id can reach course_id (which would create a cycle)
        # Start DFS from prerequisite_id and see if we can reach course_id
        visited = set()
        path = []
        
        def dfs(current: int, target: int, current_path: List[int]) -> Optional[List[int]]:
            """DFS to find if target is reachable from current"""
            if current == target and len(current_path) > 0:
                # Found a cycle
                return current_path + [current]
            
            if current in visited:
                return None
            
            visited.add(current)
            current_path.append(current)
            
            # Explore all prerequisites of current course
            if current in prerequisites_map:
                for prereq in prerequisites_map[current]:
                    result = dfs(prereq, target, current_path.copy())
                    if result:
                        return result
            
            return None
        
        # Check if we can reach course_id from prerequisite_id
        cycle_path = dfs(prerequisite_id, course_id, [])
        
        if cycle_path:
            return True, cycle_path
        
        return False, None
    
    async def get_prerequisites(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List all prerequisite relationships with optional filters.
        
        Requirements: 7.1
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary with filter criteria:
                - course_id: Filter by course
                - prerequisite_id: Filter by prerequisite
                
        Returns:
            Tuple of (list of prerequisite dictionaries, total count)
        """
        query = course_prerequisites.select()
        
        if filters:
            conditions = []
            if filters.get("course_id"):
                conditions.append(course_prerequisites.c.course_id == filters["course_id"])
            
            if filters.get("prerequisite_id"):
                conditions.append(course_prerequisites.c.prerequisite_id == filters["prerequisite_id"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = query.with_only_columns(course_prerequisites.c.id)
        total_count = len(self.db.execute(count_query).fetchall())
        
        # Get paginated results
        results = self.db.execute(query.offset(skip).limit(limit)).fetchall()
        
        prerequisites = []
        for row in results:
            prerequisites.append({
                "id": row.id,
                "course_id": row.course_id,
                "prerequisite_id": row.prerequisite_id,
                "created_at": row.created_at
            })
        
        return prerequisites, total_count
    
    async def delete_prerequisite(
        self, 
        course_id: int, 
        prerequisite_id: int
    ) -> Dict[str, Any]:
        """
        Delete prerequisite relationship.
        
        Requirements: 7.3
        
        Args:
            course_id: ID of the course
            prerequisite_id: ID of the prerequisite to remove
            
        Returns:
            Dictionary with deletion result
            
        Raises:
            ValueError: If prerequisite relationship not found
        """
        # Check if prerequisite relationship exists
        existing = self.db.execute(
            course_prerequisites.select().where(
                and_(
                    course_prerequisites.c.course_id == course_id,
                    course_prerequisites.c.prerequisite_id == prerequisite_id
                )
            )
        ).first()
        
        if not existing:
            raise ValueError(
                f"Prerequisite relationship not found between course {course_id} and prerequisite {prerequisite_id}"
            )
        
        # Delete the relationship
        stmt = course_prerequisites.delete().where(
            and_(
                course_prerequisites.c.course_id == course_id,
                course_prerequisites.c.prerequisite_id == prerequisite_id
            )
        )
        self.db.execute(stmt)
        self.db.commit()
        
        return {
            "success": True,
            "message": "Prerequisite relationship has been deleted"
        }
    
    async def get_prerequisite_chain(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get complete prerequisite chain for a course using graph traversal.
        Returns all direct and indirect prerequisites organized by level.
        
        Requirements: 7.4
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of dictionaries with prerequisite information organized by dependency level
        """
        # Use BFS to get prerequisites level by level
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.is_deleted == False
        ).first()
        
        if not course:
            return []
        
        # Build prerequisite chain using BFS
        visited = set()
        queue = deque([(course_id, 0)])  # (course_id, level)
        chain = []
        
        while queue:
            current_id, level = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get current course
            current_course = self.db.query(Course).filter(
                Course.id == current_id,
                Course.is_deleted == False
            ).first()
            
            if not current_course:
                continue
            
            # Get direct prerequisites of current course
            prereq_rels = self.db.execute(
                course_prerequisites.select().where(
                    course_prerequisites.c.course_id == current_id
                )
            ).fetchall()
            
            for prereq_rel in prereq_rels:
                prereq_course = self.db.query(Course).filter(
                    Course.id == prereq_rel.prerequisite_id,
                    Course.is_deleted == False
                ).first()
                
                if prereq_course and prereq_course.id not in visited:
                    chain.append({
                        "level": level + 1,
                        "course_id": prereq_course.id,
                        "course_name": prereq_course.name,
                        "course_code": prereq_course.code,
                        "semester_number": prereq_course.semester.semester_number,
                        "ects_credits": prereq_course.ects_credits,
                        "required_by_id": current_id,
                        "required_by_name": current_course.name
                    })
                    queue.append((prereq_course.id, level + 1))
        
        # Sort by level and then by semester
        chain.sort(key=lambda x: (x["level"], x["semester_number"]))
        
        return chain
    
    async def batch_create_prerequisites(
        self, 
        prerequisites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch create multiple prerequisite relationships.
        
        Requirements: 7.1
        
        Args:
            prerequisites: List of dictionaries with 'course_id' and 'prerequisite_id'
            
        Returns:
            Dictionary with summary of creations (success_count, error_count, errors)
        """
        success_count = 0
        error_count = 0
        errors = []
        
        for i, prereq_data in enumerate(prerequisites):
            course_id = prereq_data.get("course_id")
            prerequisite_id = prereq_data.get("prerequisite_id")
            
            if not course_id or not prerequisite_id:
                error_count += 1
                errors.append({
                    "index": i,
                    "error": "Missing course_id or prerequisite_id",
                    "data": prereq_data
                })
                continue
            
            try:
                result = await self.create_prerequisite(course_id, prerequisite_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "index": i,
                    "course_id": course_id,
                    "prerequisite_id": prerequisite_id,
                    "error": str(e)
                })
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    async def batch_delete_prerequisites(
        self, 
        prerequisites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch delete multiple prerequisite relationships.
        
        Requirements: 7.3
        
        Args:
            prerequisites: List of dictionaries with 'course_id' and 'prerequisite_id'
            
        Returns:
            Dictionary with summary of deletions (success_count, error_count, errors)
        """
        success_count = 0
        error_count = 0
        errors = []
        
        for i, prereq_data in enumerate(prerequisites):
            course_id = prereq_data.get("course_id")
            prerequisite_id = prereq_data.get("prerequisite_id")
            
            if not course_id or not prerequisite_id:
                error_count += 1
                errors.append({
                    "index": i,
                    "error": "Missing course_id or prerequisite_id",
                    "data": prereq_data
                })
                continue
            
            try:
                await self.delete_prerequisite(course_id, prerequisite_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "index": i,
                    "course_id": course_id,
                    "prerequisite_id": prerequisite_id,
                    "error": str(e)
                })
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
