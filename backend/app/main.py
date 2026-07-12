"""
AI Study Planner v2 — FastAPI Main Application

Includes:
  - Student-facing API (auth, profile, subjects, study plans, exports, notifications)
  - Super Admin Platform API (/api/v1/admin/*)

Super Admin Platform modules:
  universities, campuses, study_programs, academic_tracks, semesters,
  teaching_units, courses, prerequisites, validation_rules, imports,
  dashboard, audit, exports, search, roles, settings
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1 import api_router
from app.services.background_jobs import background_jobs

# ---------------------------------------------------------------------------
# OpenAPI tags — order controls rendering in /api/docs
# ---------------------------------------------------------------------------
OPENAPI_TAGS = [
    # Student-facing
    {"name": "auth",            "description": "User authentication — login, register, refresh token"},
    {"name": "profile",         "description": "Student profile management"},
    {"name": "subjects",        "description": "Course/subject management for students"},
    {"name": "availabilities",  "description": "Student availability time-blocks"},
    {"name": "constraints",     "description": "Student study constraints"},
    {"name": "study-plans",     "description": "AI-generated personalised study plan management"},
    {"name": "exports",         "description": "Student study-plan exports (PDF / iCal)"},
    {"name": "notifications",   "description": "In-app notifications"},

    # Super Admin Platform
    {"name": "admin",           "description": "🔐 Super Admin Platform — requires admin role"},
    {"name": "universities",    "description": "University CRUD (Super Admin / University Admin)"},
    {"name": "campuses",        "description": "Campus CRUD scoped to a university"},
    {"name": "programs",        "description": "Study programme CRUD"},
    {"name": "tracks",          "description": "Academic track CRUD and ECTS hierarchy validation"},
    {"name": "semesters",       "description": "Semester CRUD"},
    {"name": "teaching-units",  "description": "Teaching unit CRUD"},
    {"name": "courses",         "description": "Course CRUD and batch operations"},
    {"name": "prerequisites",   "description": "Course prerequisite relationships (with circular-dependency detection)"},
    {"name": "validation-rules","description": "Track validation rules (ECTS rules)"},
    {"name": "imports",         "description": "Bulk Excel import — upload → validate → preview → execute → rollback"},
    {"name": "dashboard",       "description": "Aggregate statistics, activity feed, and system health checks"},
    {"name": "audit",           "description": "Audit log queries and exports (Super Admin only)"},
    {"name": "exports",         "description": "Curriculum exports (Excel / PDF) and JSON reports"},
    {"name": "search",          "description": "Global cross-entity search with relevance scoring"},
    {"name": "roles",           "description": "Role assignment management (Super Admin only)"},
    {"name": "settings",        "description": "System configuration settings (Super Admin only)"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Startup:
      - Creates the uploads/imports directory used by the bulk import router
      - Starts background jobs (study plan cleanup, notification dispatch)

    Shutdown:
      - Gracefully stops background jobs
    """
    # Ensure upload directory exists
    upload_dir = Path("uploads") / "imports"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Start background jobs
    await background_jobs.start()

    yield

    # Stop background jobs
    await background_jobs.stop()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Study Planner API",
    description=(
        "**AI Study Planner v2** — Intelligent personalised weekly study schedule generator "
        "for German university students.\n\n"
        "### Super Admin Platform\n"
        "All endpoints under `/api/v1/admin/` are restricted to authenticated admin users. "
        "Three RBAC roles are supported:\n"
        "- **super_admin** — full access to all universities and configuration\n"
        "- **university_admin** — scoped to one or more universities\n"
        "- **program_coordinator** — scoped to one or more study programmes\n\n"
        "Authenticate via `POST /api/v1/auth/login` and pass the `access_token` as a "
        "`Bearer` token in the `Authorization` header."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# Admin router is mounted inside api_router at /api/v1/admin (via v1/__init__.py)
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"], include_in_schema=False)
async def root():
    """Welcome / liveness probe."""
    return {
        "message": "AI Study Planner API v2",
        "version": "2.0.0",
        "docs": "/api/docs",
        "admin_platform": "/api/v1/admin",
    }


@app.get("/health", tags=["root"], include_in_schema=False)
async def health_check():
    """Kubernetes / load-balancer health probe."""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
