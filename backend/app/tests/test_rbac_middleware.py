"""
Unit tests for RBAC middleware decorators and access control functions

Requirements: 11.1-11.9
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack
from app.models.university import University
from app.models.audit_log import AuditLog
from app.middleware.rbac import (
    check_university_access,
    check_program_access,
    get_accessible_universities,
    get_accessible_programs,
    has_role,
    is_super_admin,
    ROLE_SUPER_ADMIN,
    ROLE_UNIVERSITY_ADMIN,
    ROLE_PROGRAM_COORDINATOR,
    _log_access_denial
)


@pytest.fixture
def super_admin_role(db_session: Session) -> AdminRole:
    """Create Super Admin role"""
    role = AdminRole(
        name=ROLE_SUPER_ADMIN,
        display_name="Super Admin",
        description="Full system access",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def university_admin_role(db_session: Session) -> AdminRole:
    """Create University Admin role"""
    role = AdminRole(
        name=ROLE_UNIVERSITY_ADMIN,
        display_name="University Admin",
        description="University-scoped access",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def program_coordinator_role(db_session: Session) -> AdminRole:
    """Create Program Coordinator role"""
    role = AdminRole(
        name=ROLE_PROGRAM_COORDINATOR,
        display_name="Program Coordinator",
        description="Program-scoped access",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_university(db_session: Session) -> University:
    """Create test university"""
    university = University(
        name="Test University",
        country="Germany",
        is_deleted=False
    )
    db_session.add(university)
    db_session.commit()
    db_session.refresh(university)
    return university


@pytest.fixture
def test_university_2(db_session: Session) -> University:
    """Create second test university"""
    university = University(
        name="Test University 2",
        country="Germany",
        is_deleted=False
    )
    db_session.add(university)
    db_session.commit()
    db_session.refresh(university)
    return university


@pytest.fixture
def test_program(db_session: Session) -> StudyProgram:
    """Create test study program"""
    program = StudyProgram(
        name="Computer Science",
        description="CS program",
        code="CS",
        is_deleted=False
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


@pytest.fixture
def test_track(db_session: Session, test_university: University, test_program: StudyProgram) -> AcademicTrack:
    """Create test academic track linking program to university"""
    from app.models.academic_track import TrackLevel
    from datetime import datetime, timezone
    track = AcademicTrack(
        name="Bachelor CS",
        level=TrackLevel.BACHELOR,
        study_program_id=test_program.id,
        total_ects_required=180,
        is_deleted=False
    )
    db_session.add(track)
    db_session.commit()
    db_session.refresh(track)
    
    # Link program to university via university_programs association table
    from sqlalchemy import text
    db_session.execute(
        text("INSERT INTO university_programs (university_id, study_program_id, created_at) VALUES (:univ_id, :prog_id, :created_at)"),
        {"univ_id": test_university.id, "prog_id": test_program.id, "created_at": datetime.now(timezone.utc)}
    )
    db_session.commit()
    
    return track


class TestCheckUniversityAccess:
    """Test check_university_access function - Requirements 11.1, 11.2, 11.7, 11.9"""
    
    def test_super_admin_has_access_to_all_universities(
        self, 
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole,
        test_university: University
    ):
        """Super Admin should have access to all universities"""
        # Assign super admin role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Super admin should have access
        assert check_university_access(test_user, test_university.id, db_session) is True
    
    def test_university_admin_has_access_to_assigned_university(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole,
        test_university: University
    ):
        """University Admin should have access to their assigned university"""
        # Assign university admin role with specific university
        user_role = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university.id,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should have access to assigned university
        assert check_university_access(test_user, test_university.id, db_session) is True
    
    def test_university_admin_no_access_to_other_university(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole,
        test_university: University,
        test_university_2: University
    ):
        """University Admin should not have access to other universities"""
        # Assign university admin role with specific university
        user_role = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university.id,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should NOT have access to other university
        assert check_university_access(test_user, test_university_2.id, db_session) is False
    
    def test_program_coordinator_has_access_to_university_with_their_program(
        self,
        db_session: Session,
        test_user: User,
        program_coordinator_role: AdminRole,
        test_university: University,
        test_program: StudyProgram,
        test_track: AcademicTrack
    ):
        """Program Coordinator should have access to university containing their program"""
        # Assign program coordinator role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=program_coordinator_role.id,
            university_id=None,
            program_id=test_program.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should have access to university containing the program
        assert check_university_access(test_user, test_university.id, db_session) is True
    
    def test_user_with_no_roles_has_no_access(
        self,
        db_session: Session,
        test_user: User,
        test_university: University
    ):
        """User with no roles should not have access"""
        assert check_university_access(test_user, test_university.id, db_session) is False


class TestCheckProgramAccess:
    """Test check_program_access function - Requirements 11.1, 11.2, 11.3, 11.8, 11.9"""
    
    def test_super_admin_has_access_to_all_programs(
        self,
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole,
        test_program: StudyProgram
    ):
        """Super Admin should have access to all programs"""
        # Assign super admin role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Super admin should have access
        assert check_program_access(test_user, test_program.id, db_session) is True
    
    def test_university_admin_has_access_to_programs_in_their_university(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole,
        test_university: University,
        test_program: StudyProgram,
        test_track: AcademicTrack
    ):
        """University Admin should have access to programs in their university"""
        # Assign university admin role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university.id,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should have access to program in their university
        assert check_program_access(test_user, test_program.id, db_session) is True
    
    def test_program_coordinator_has_access_to_assigned_program(
        self,
        db_session: Session,
        test_user: User,
        program_coordinator_role: AdminRole,
        test_program: StudyProgram
    ):
        """Program Coordinator should have access to their assigned program"""
        # Assign program coordinator role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=program_coordinator_role.id,
            university_id=None,
            program_id=test_program.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should have access to assigned program
        assert check_program_access(test_user, test_program.id, db_session) is True
    
    def test_program_coordinator_no_access_to_other_programs(
        self,
        db_session: Session,
        test_user: User,
        program_coordinator_role: AdminRole,
        test_program: StudyProgram
    ):
        """Program Coordinator should not have access to other programs"""
        # Create another program
        other_program = StudyProgram(
            name="Physics",
            description="Physics program",
            code="PHY",
            is_deleted=False
        )
        db_session.add(other_program)
        db_session.commit()
        
        # Assign program coordinator role to first program
        user_role = UserRole(
            user_id=test_user.id,
            role_id=program_coordinator_role.id,
            university_id=None,
            program_id=test_program.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should NOT have access to other program
        assert check_program_access(test_user, other_program.id, db_session) is False


class TestGetAccessibleUniversities:
    """Test get_accessible_universities function - Requirement 11.9"""
    
    def test_super_admin_returns_none_for_all_access(
        self,
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole
    ):
        """Super Admin should return None indicating access to all universities"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        result = get_accessible_universities(test_user, db_session)
        assert result is None  # None means all access
    
    def test_university_admin_returns_assigned_universities(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole,
        test_university: University,
        test_university_2: University
    ):
        """University Admin should return list of assigned universities"""
        # Assign two universities
        user_role_1 = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university.id,
            program_id=None
        )
        user_role_2 = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university_2.id,
            program_id=None
        )
        db_session.add(user_role_1)
        db_session.add(user_role_2)
        db_session.commit()
        
        result = get_accessible_universities(test_user, db_session)
        assert result is not None
        assert set(result) == {test_university.id, test_university_2.id}
    
    def test_program_coordinator_returns_universities_with_their_programs(
        self,
        db_session: Session,
        test_user: User,
        program_coordinator_role: AdminRole,
        test_university: University,
        test_program: StudyProgram,
        test_track: AcademicTrack
    ):
        """Program Coordinator should return universities containing their programs"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=program_coordinator_role.id,
            university_id=None,
            program_id=test_program.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        result = get_accessible_universities(test_user, db_session)
        assert result is not None
        assert test_university.id in result


class TestGetAccessiblePrograms:
    """Test get_accessible_programs function - Requirement 11.9"""
    
    def test_super_admin_returns_none_for_all_access(
        self,
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole
    ):
        """Super Admin should return None indicating access to all programs"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        result = get_accessible_programs(test_user, db_session)
        assert result is None
    
    def test_university_admin_returns_none_for_all_programs_in_scope(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole,
        test_university: University
    ):
        """University Admin should return None (all programs in their university scope)"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=test_university.id,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        result = get_accessible_programs(test_user, db_session)
        assert result is None
    
    def test_program_coordinator_returns_assigned_programs(
        self,
        db_session: Session,
        test_user: User,
        program_coordinator_role: AdminRole,
        test_program: StudyProgram
    ):
        """Program Coordinator should return list of assigned programs"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=program_coordinator_role.id,
            university_id=None,
            program_id=test_program.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        result = get_accessible_programs(test_user, db_session)
        assert result is not None
        assert test_program.id in result


class TestHasRole:
    """Test has_role and is_super_admin functions - Requirements 11.1, 11.4"""
    
    def test_has_role_returns_true_for_assigned_role(
        self,
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole
    ):
        """has_role should return True for assigned role"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        assert has_role(test_user, ROLE_SUPER_ADMIN, db_session) is True
    
    def test_has_role_returns_false_for_unassigned_role(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole
    ):
        """has_role should return False for unassigned role"""
        assert has_role(test_user, ROLE_UNIVERSITY_ADMIN, db_session) is False
    
    def test_is_super_admin_returns_true_for_super_admin(
        self,
        db_session: Session,
        test_user: User,
        super_admin_role: AdminRole
    ):
        """is_super_admin should return True for super admin"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=super_admin_role.id,
            university_id=None,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        assert is_super_admin(test_user, db_session) is True
    
    def test_is_super_admin_returns_false_for_non_super_admin(
        self,
        db_session: Session,
        test_user: User,
        university_admin_role: AdminRole
    ):
        """is_super_admin should return False for non-super admin"""
        user_role = UserRole(
            user_id=test_user.id,
            role_id=university_admin_role.id,
            university_id=1,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        assert is_super_admin(test_user, db_session) is False


class TestLogAccessDenial:
    """Test _log_access_denial function - Requirements 11.7, 11.8"""
    
    @pytest.mark.asyncio
    async def test_log_access_denial_creates_audit_log(
        self,
        db_session: Session,
        test_user: User
    ):
        """Access denial should be logged to audit log"""
        await _log_access_denial(
            db=db_session,
            user_id=test_user.id,
            endpoint="test_endpoint",
            required_roles=["super_admin"],
            resource_type="university",
            resource_id=1
        )
        
        # Check audit log was created
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.user_id == test_user.id,
            AuditLog.operation == "access_denied"
        ).first()
        
        assert audit_log is not None
        assert audit_log.entity_type == "access_control"
        assert audit_log.after_value["endpoint"] == "test_endpoint"
        assert audit_log.after_value["required_roles"] == ["super_admin"]
        assert audit_log.after_value["resource_type"] == "university"
        assert audit_log.after_value["resource_id"] == 1
    
    @pytest.mark.asyncio
    async def test_log_access_denial_handles_errors_gracefully(
        self,
        db_session: Session,
        test_user: User
    ):
        """Access denial logging should not fail the request on errors"""
        # Close the session to simulate error
        db_session.close()
        
        # Should not raise exception
        await _log_access_denial(
            db=db_session,
            user_id=test_user.id,
            endpoint="test_endpoint"
        )


class TestInactiveRoles:
    """Test that inactive roles are not considered - Requirement 11.4"""
    
    def test_inactive_role_not_granted_access(
        self,
        db_session: Session,
        test_user: User,
        test_university: University
    ):
        """Inactive roles should not grant access"""
        # Create inactive role
        inactive_role = AdminRole(
            name="inactive_admin",
            display_name="Inactive Admin",
            description="Inactive role",
            is_active=False
        )
        db_session.add(inactive_role)
        db_session.commit()
        
        # Assign inactive role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=inactive_role.id,
            university_id=test_university.id,
            program_id=None
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Should NOT have access with inactive role
        assert check_university_access(test_user, test_university.id, db_session) is False
        assert has_role(test_user, "inactive_admin", db_session) is False
