"""
Role-Based Access Control (RBAC) Middleware

This module provides decorators and utility functions for enforcing role-based
access control throughout the Super Admin Platform. It supports three roles:
- Super Admin: Full access to all universities and programs
- University Admin: Access limited to specific universities
- Program Coordinator: Access limited to specific programs

Requirements: 11.1-11.9
"""
from functools import wraps
from typing import List, Callable, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_role import UserRole
from app.models.admin_role import AdminRole
from app.models.audit_log import AuditLog
from datetime import datetime, timezone


# Role name constants
ROLE_SUPER_ADMIN = "super_admin"
ROLE_UNIVERSITY_ADMIN = "university_admin"
ROLE_PROGRAM_COORDINATOR = "program_coordinator"


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Decorator to enforce role-based access control on API endpoints.
    
    This decorator checks if the current user has one of the required roles.
    It should be used on FastAPI route handlers after the authentication
    dependency (get_current_user).
    
    Requirements: 11.1, 11.2, 11.3, 11.4
    
    Args:
        allowed_roles: List of role names that can access the endpoint
                      e.g., ['super_admin', 'university_admin']
    
    Returns:
        Decorated function with role enforcement
    
    Raises:
        HTTPException 403: If user doesn't have any of the required roles
    
    Example:
        @router.get("/universities")
        @require_role(["super_admin", "university_admin"])
        async def get_universities(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user and db from kwargs
            current_user: Optional[User] = kwargs.get('current_user')
            db: Optional[Session] = kwargs.get('db')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check if user has any of the allowed roles
            user_roles = db.query(UserRole).filter(
                UserRole.user_id == current_user.id
            ).join(AdminRole).filter(
                AdminRole.name.in_(allowed_roles),
                AdminRole.is_active == True
            ).all()
            
            if not user_roles:
                # Log denied access attempt (Requirement 11.7, 11.8)
                await _log_access_denial(
                    db=db,
                    user_id=current_user.id,
                    required_roles=allowed_roles,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
                )
            
            # Store user roles in kwargs for potential use in the endpoint
            kwargs['user_roles'] = user_roles
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_university_access(user: User, university_id: int, db: Session) -> bool:
    """
    Check if user has access to a specific university.
    
    Super Admins have access to all universities.
    University Admins only have access to their assigned universities.
    Program Coordinators have access to universities containing their programs.
    
    Requirements: 11.2, 11.7, 11.9
    
    Args:
        user: Current authenticated user
        university_id: ID of the university to check access for
        db: Database session
    
    Returns:
        True if user has access to the university, False otherwise
    
    Example:
        if not check_university_access(current_user, university_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
    """
    # Get user's roles
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    for user_role in user_roles:
        role_name = user_role.role.name
        
        # Super Admin has access to all universities (Requirement 11.1)
        if role_name == ROLE_SUPER_ADMIN:
            return True
        
        # University Admin has access to their assigned universities (Requirement 11.2)
        if role_name == ROLE_UNIVERSITY_ADMIN:
            if user_role.university_id == university_id:
                return True
        
        # Program Coordinator has access to universities containing their programs (Requirement 11.3)
        if role_name == ROLE_PROGRAM_COORDINATOR:
            if user_role.program_id:
                # Check if the program is linked to this university via the association table
                from app.models.study_program import StudyProgram, university_programs
                from sqlalchemy import select
                
                # Query the association table for the link
                stmt = select(university_programs).where(
                    university_programs.c.study_program_id == user_role.program_id,
                    university_programs.c.university_id == university_id
                )
                result = db.execute(stmt).first()
                
                if result:
                    return True
    
    return False


def check_program_access(user: User, program_id: int, db: Session) -> bool:
    """
    Check if user has access to a specific program.
    
    Super Admins have access to all programs.
    University Admins have access to programs in their universities.
    Program Coordinators only have access to their assigned programs.
    
    Requirements: 11.3, 11.8, 11.9
    
    Args:
        user: Current authenticated user
        program_id: ID of the program to check access for
        db: Database session
    
    Returns:
        True if user has access to the program, False otherwise
    
    Example:
        if not check_program_access(current_user, program_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
    """
    # Get user's roles
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    for user_role in user_roles:
        role_name = user_role.role.name
        
        # Super Admin has access to all programs (Requirement 11.1)
        if role_name == ROLE_SUPER_ADMIN:
            return True
        
        # University Admin has access to programs in their universities (Requirement 11.2)
        if role_name == ROLE_UNIVERSITY_ADMIN:
            if user_role.university_id:
                # Check if the program is linked to this university via the association table
                from app.models.study_program import university_programs
                from sqlalchemy import select
                
                stmt = select(university_programs).where(
                    university_programs.c.study_program_id == program_id,
                    university_programs.c.university_id == user_role.university_id
                )
                result = db.execute(stmt).first()
                
                if result:
                    return True
        
        # Program Coordinator has access to their assigned programs (Requirement 11.3)
        if role_name == ROLE_PROGRAM_COORDINATOR:
            if user_role.program_id == program_id:
                return True
    
    return False


def get_accessible_universities(user: User, db: Session) -> List[int]:
    """
    Get list of university IDs that the user has access to.
    
    This is useful for filtering queries to only show permitted data.
    
    Requirements: 11.9
    
    Args:
        user: Current authenticated user
        db: Database session
    
    Returns:
        List of university IDs the user can access.
        Empty list means no access, None means all access (Super Admin)
    
    Example:
        accessible_unis = get_accessible_universities(current_user, db)
        if accessible_unis is None:
            # Super Admin - show all
            query = db.query(University)
        else:
            # Filtered access
            query = db.query(University).filter(University.id.in_(accessible_unis))
    """
    # Get user's roles
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    # Check if user is Super Admin
    for user_role in user_roles:
        if user_role.role.name == ROLE_SUPER_ADMIN:
            return None  # None indicates access to all universities
    
    # Collect accessible university IDs
    accessible_ids = set()
    
    for user_role in user_roles:
        role_name = user_role.role.name
        
        # University Admin has access to their assigned universities
        if role_name == ROLE_UNIVERSITY_ADMIN and user_role.university_id:
            accessible_ids.add(user_role.university_id)
        
        # Program Coordinator has access to universities containing their programs
        if role_name == ROLE_PROGRAM_COORDINATOR and user_role.program_id:
            from app.models.study_program import university_programs
            from sqlalchemy import select
            
            # Get all universities linked to this program
            stmt = select(university_programs.c.university_id).where(
                university_programs.c.study_program_id == user_role.program_id
            )
            results = db.execute(stmt).fetchall()
            
            for row in results:
                accessible_ids.add(row[0])
    
    return list(accessible_ids)


def get_accessible_programs(user: User, db: Session) -> Optional[List[int]]:
    """
    Get list of program IDs that the user has access to.
    
    This is useful for filtering queries to only show permitted data.
    
    Requirements: 11.9
    
    Args:
        user: Current authenticated user
        db: Database session
    
    Returns:
        List of program IDs the user can access.
        None means all access (Super Admin or University Admin with university scope)
    
    Example:
        accessible_programs = get_accessible_programs(current_user, db)
        if accessible_programs is None:
            # Show all programs
            query = db.query(StudyProgram)
        else:
            # Filtered access
            query = db.query(StudyProgram).filter(StudyProgram.id.in_(accessible_programs))
    """
    # Get user's roles
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    # Check if user is Super Admin or University Admin (they see all programs in their scope)
    for user_role in user_roles:
        if user_role.role.name in [ROLE_SUPER_ADMIN, ROLE_UNIVERSITY_ADMIN]:
            return None  # None indicates access to all programs (in their scope)
    
    # Collect accessible program IDs for Program Coordinators
    accessible_ids = set()
    
    for user_role in user_roles:
        if user_role.role.name == ROLE_PROGRAM_COORDINATOR and user_role.program_id:
            accessible_ids.add(user_role.program_id)
    
    return list(accessible_ids) if accessible_ids else []


def require_university_access(university_id_param: str = "university_id") -> Callable:
    """
    Decorator to enforce university-level access control.
    
    This decorator checks if the user has access to a specific university
    by extracting the university_id from the endpoint parameters.
    
    Requirements: 11.7
    
    Args:
        university_id_param: Name of the parameter containing university_id
                            (default: "university_id")
    
    Returns:
        Decorated function with university access enforcement
    
    Raises:
        HTTPException 403: If user doesn't have access to the university
    
    Example:
        @router.get("/universities/{university_id}/campuses")
        @require_university_access()
        async def get_campuses(
            university_id: int,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[User] = kwargs.get('current_user')
            db: Optional[Session] = kwargs.get('db')
            university_id: Optional[int] = kwargs.get(university_id_param)
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if university_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {university_id_param} parameter"
                )
            
            # Check access
            if not check_university_access(current_user, university_id, db):
                # Log denied access attempt
                await _log_access_denial(
                    db=db,
                    user_id=current_user.id,
                    resource_type="university",
                    resource_id=university_id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to university {university_id}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_program_access(program_id_param: str = "program_id") -> Callable:
    """
    Decorator to enforce program-level access control.
    
    This decorator checks if the user has access to a specific program
    by extracting the program_id from the endpoint parameters.
    
    Requirements: 11.8
    
    Args:
        program_id_param: Name of the parameter containing program_id
                         (default: "program_id")
    
    Returns:
        Decorated function with program access enforcement
    
    Raises:
        HTTPException 403: If user doesn't have access to the program
    
    Example:
        @router.get("/programs/{program_id}/courses")
        @require_program_access()
        async def get_courses(
            program_id: int,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[User] = kwargs.get('current_user')
            db: Optional[Session] = kwargs.get('db')
            program_id: Optional[int] = kwargs.get(program_id_param)
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if program_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {program_id_param} parameter"
                )
            
            # Check access
            if not check_program_access(current_user, program_id, db):
                # Log denied access attempt
                await _log_access_denial(
                    db=db,
                    user_id=current_user.id,
                    resource_type="program",
                    resource_id=program_id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to program {program_id}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def _log_access_denial(
    db: Session,
    user_id: int,
    endpoint: str,
    required_roles: Optional[List[str]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None
) -> None:
    """
    Log denied access attempts to the audit log.
    
    Requirements: 11.7, 11.8
    
    Args:
        db: Database session
        user_id: ID of the user whose access was denied
        endpoint: Name of the endpoint that was accessed
        required_roles: List of roles required for access (if role-based denial)
        resource_type: Type of resource (e.g., 'university', 'program')
        resource_id: ID of the specific resource
    """
    try:
        description_parts = [f"Access denied to endpoint '{endpoint}'"]
        
        if required_roles:
            description_parts.append(f"Required roles: {', '.join(required_roles)}")
        
        if resource_type and resource_id:
            description_parts.append(f"Resource: {resource_type} #{resource_id}")
        
        description = " | ".join(description_parts)
        
        audit_log = AuditLog(
            entity_type="access_control",
            entity_id=user_id,
            operation="access_denied",
            before_value=None,
            after_value={
                "endpoint": endpoint,
                "required_roles": required_roles,
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            description=description
        )
        
        db.add(audit_log)
        db.commit()
    except Exception as e:
        # Don't fail the request if audit logging fails
        # But rollback the session to prevent issues
        db.rollback()
        print(f"Warning: Failed to log access denial: {e}")


def has_role(user: User, role_name: str, db: Session) -> bool:
    """
    Check if a user has a specific role.
    
    Requirements: 11.4
    
    Args:
        user: User to check
        role_name: Name of the role to check for
        db: Database session
    
    Returns:
        True if user has the role, False otherwise
    
    Example:
        if has_role(current_user, "super_admin", db):
            # Allow special operations
            pass
    """
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.name == role_name,
        AdminRole.is_active == True
    ).first()
    
    return user_role is not None


def is_super_admin(user: User, db: Session) -> bool:
    """
    Check if a user is a Super Admin.
    
    Requirements: 11.1
    
    Args:
        user: User to check
        db: Database session
    
    Returns:
        True if user is a Super Admin, False otherwise
    
    Example:
        if is_super_admin(current_user, db):
            # Allow full system access
            pass
    """
    return has_role(user, ROLE_SUPER_ADMIN, db)
