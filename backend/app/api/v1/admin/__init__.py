"""
Admin API routes for Super Admin Platform
"""
from fastapi import APIRouter
from app.api.v1.admin import (
    universities,
    campuses,
    study_programs,
    academic_tracks,
    semesters,
    teaching_units,
    courses,
    prerequisites,
    validation_rules,
    imports,
    dashboard,
    audit,
    exports,
    search,
    roles,
    settings,
)

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Include all sub-routers
admin_router.include_router(universities.router, prefix="/universities", tags=["universities"])
admin_router.include_router(campuses.router, prefix="/campuses", tags=["campuses"])
admin_router.include_router(study_programs.router, prefix="/programs", tags=["programs"])
admin_router.include_router(academic_tracks.router, prefix="/tracks", tags=["tracks"])
admin_router.include_router(semesters.router, prefix="/semesters", tags=["semesters"])
admin_router.include_router(teaching_units.router, prefix="/teaching-units", tags=["teaching-units"])
admin_router.include_router(courses.router, prefix="/courses", tags=["courses"])
admin_router.include_router(prerequisites.router, prefix="/prerequisites", tags=["prerequisites"])
admin_router.include_router(validation_rules.router, prefix="/validation-rules", tags=["validation-rules"])
admin_router.include_router(imports.router, prefix="/imports", tags=["imports"])
admin_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
admin_router.include_router(audit.router, prefix="/audit", tags=["audit"])
admin_router.include_router(exports.router, prefix="/exports", tags=["exports"])
admin_router.include_router(search.router, prefix="/search", tags=["search"])
admin_router.include_router(roles.router, prefix="/roles", tags=["roles"])
admin_router.include_router(settings.router, prefix="/settings", tags=["settings"])

__all__ = ["admin_router"]
