"""Database models package"""
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.generation_log import GenerationLog
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.admin_role import AdminRole
from app.models.admin_permission import AdminPermission
from app.models.user_role import UserRole
from app.models.university import University
from app.models.campus import Campus
from app.models.study_program import StudyProgram
from app.models.academic_track import AcademicTrack, TrackLevel
from app.models.semester import Semester
from app.models.teaching_unit import TeachingUnit
from app.models.course import Course
from app.models.validation_rule import ValidationRule, RuleType

# NEW: Academic tracking models
from app.models.grade import Grade
from app.models.exam import Exam
from app.models.ects_progress import ECTSProgress
from app.models.risk_score import RiskScore
from app.models.priority_score import PriorityScore
from app.models.student_course_enrollment import StudentCourseEnrollment

__all__ = [
    "User",
    "StudentProfile",
    "Subject",
    "Availability",
    "Constraint",
    "StudyPlan",
    "StudySession",
    "GenerationLog",
    "Notification",
    "AuditLog",
    "AdminRole",
    "AdminPermission",
    "UserRole",
    "University",
    "Campus",
    "StudyProgram",
    "AcademicTrack",
    "TrackLevel",
    "Semester",
    "TeachingUnit",
    "Course",
    "ValidationRule",
    "RuleType",
    # NEW
    "Grade",
    "Exam",
    "ECTSProgress",
    "RiskScore",
    "PriorityScore",
    "StudentCourseEnrollment",
]
