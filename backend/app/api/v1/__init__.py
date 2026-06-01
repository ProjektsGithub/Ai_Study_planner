"""
API v1 routes
"""
from fastapi import APIRouter
from app.api.v1 import auth, profile, subjects, availabilities, constraints, study_plans, exports, notifications

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(subjects.router)
api_router.include_router(availabilities.router)
api_router.include_router(constraints.router)
api_router.include_router(study_plans.router)
api_router.include_router(exports.router)
api_router.include_router(notifications.router)

__all__ = ["api_router"]
