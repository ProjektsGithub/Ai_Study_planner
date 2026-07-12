"""
API v1 routes
"""
from fastapi import APIRouter
from app.api.v1 import auth, profile, subjects, availabilities, constraints, study_plans, exports, notifications, chat
from app.api.v1.admin import admin_router

# NEW: Academic tracking routers
from app.api.v1 import academic_profile, grades, exams, ects, analysis, ai_context, plan_optimizer
from app.api.v1 import enrollments
from app.api.v1 import setup

api_router = APIRouter()

# Existing routers
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(subjects.router)
api_router.include_router(availabilities.router)
api_router.include_router(constraints.router)
api_router.include_router(study_plans.router)
api_router.include_router(exports.router)
api_router.include_router(notifications.router)
api_router.include_router(chat.router)             # /api/v1/chat

# Include admin router (Super Admin Platform)
api_router.include_router(admin_router)

# NEW: Academic tracking routers
api_router.include_router(academic_profile.router)  # /api/v1/academic/...
api_router.include_router(grades.router)            # /api/v1/grades/...
api_router.include_router(exams.router)             # /api/v1/exams/...
api_router.include_router(ects.router)              # /api/v1/ects/...
api_router.include_router(analysis.router)          # /api/v1/analysis/...
api_router.include_router(ai_context.router)        # /api/v1/ai-context/...
api_router.include_router(plan_optimizer.router)    # /api/v1/study-plans/regenerate
api_router.include_router(enrollments.router)       # /api/v1/enrollments/...
api_router.include_router(setup.router)             # /api/v1/setup/...

__all__ = ["api_router"]
