# 📚 AI Study Planner

> Intelligent web application for generating personalized weekly study schedules for university students

## 🎯 Overview

AI Study Planner is a full-stack web application that automatically generates personalized weekly study plans using a hybrid architecture combining a deterministic planning engine with AI (Llama 3.2 + LoRA fine-tuning).

### Key Features

- **Automated Planning**: Generate balanced weekly study schedules based on your academic profile
- **Smart Prioritization**: AI-powered scheduling considering exam dates, subject difficulty, and priorities
- **Manual Editing**: Modify generated plans to fit your personal preferences
- **Plan History**: Track and restore previous planning versions
- **PDF Export**: Download printable versions of your study plans
- **Notifications**: Receive reminders for upcoming study sessions
- **Super Admin Platform**: Complete institutional management system (universities, programs, courses)
- **Bulk Import**: CSV/Excel import for courses, students, and academic data
- **Audit Logging**: Track all administrative actions and changes
- **RBAC**: Role-based access control (Student, Admin, Super Admin)

## 🏗️ Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React + TailwindCSS + Axios |
| **Backend** | FastAPI + Python 3.11+ |
| **Database** | PostgreSQL 15+ |
| **AI Service** | Llama 3.2 + LoRA (Google Colab) / Ollama (local fallback) |
| **Reverse Proxy** | Nginx |
| **Containerization** | Docker + Docker Compose |

### AI Architecture

The application uses a **hybrid AI approach** for optimal cost-effectiveness:

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Deterministic Planning Engine                │  │
│  │  • Constructs valid time slots                       │  │
│  │  • Calculates subject priorities                     │  │
│  │  • Validates constraints                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI Service (Adaptive)                   │  │
│  │                                                       │  │
│  │  Primary: Google Colab (Llama 3.2 + LoRA)          │  │
│  │  • Cost: 0-50€/month                                │  │
│  │  • Fine-tuned for study planning                    │  │
│  │  • Accessible via ngrok tunnel                      │  │
│  │                                                       │  │
│  │  Fallback: Local Ollama (Llama 3.2)                │  │
│  │  • Used when Colab unavailable                      │  │
│  │  • Development environment                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Validation Service                        │  │
│  │  • Schema validation                                 │  │
│  │  • Constraint checking                               │  │
│  │  • Auto-correction                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Why Llama 3.2 + LoRA on Google Colab?**
- **Cost-effective**: 0-50€/month vs 200-500€/month for VPS
- **Scalable**: Handles up to ~50 users before needing migration
- **Fine-tunable**: LoRA adapters for domain-specific optimization
- **Flexible**: Easy migration to VPS when user base grows

See [ARCHITECTURE_DECISIONS.md](./recap/ARCHITECTURE_DECISIONS.md) and [GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md) for details.

### Project Structure

```
AIplaning/
├── backend/                     # FastAPI backend
│   ├── alembic/                # Database migrations
│   │   ├── versions/           # 8 migration files
│   │   ├── env.py              # Migration environment
│   │   └── script.py.mako      # Migration template
│   ├── app/
│   │   ├── api/v1/             # API endpoints (19 modules)
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── study_plans.py  # Study plan management
│   │   │   ├── subjects.py     # Subject management
│   │   │   ├── availabilities.py # Availability management
│   │   │   ├── constraints.py  # Constraint management
│   │   │   ├── exams.py        # Exam management
│   │   │   ├── grades.py       # Grade management
│   │   │   ├── enrollments.py  # Course enrollments
│   │   │   ├── ects.py         # ECTS progress tracking
│   │   │   ├── profile.py      # User profile
│   │   │   ├── notifications.py # Notifications
│   │   │   ├── exports.py      # PDF export
│   │   │   ├── analysis.py     # Academic analysis
│   │   │   ├── plan_optimizer.py # Plan optimization
│   │   │   ├── ai_context.py   # AI context building
│   │   │   ├── academic_profile.py # Academic profiling
│   │   │   ├── chat.py         # AI chat interface
│   │   │   ├── setup.py        # Initial setup wizard
│   │   │   └── admin/          # Admin endpoints (17 modules)
│   │   │       ├── universities.py
│   │   │       ├── campuses.py
│   │   │       ├── study_programs.py
│   │   │       ├── courses.py
│   │   │       ├── academic_tracks.py
│   │   │       ├── teaching_units.py
│   │   │       ├── semesters.py
│   │   │       ├── prerequisites.py
│   │   │       ├── validation_rules.py
│   │   │       ├── dashboard.py
│   │   │       ├── imports.py  # CSV/Excel import
│   │   │       ├── exports.py  # Data export
│   │   │       ├── search.py   # Global search
│   │   │       ├── audit.py    # Audit logs
│   │   │       ├── roles.py    # Role management
│   │   │       └── settings.py # System settings
│   │   ├── core/               # Core configuration
│   │   │   ├── config.py       # App settings
│   │   │   ├── database.py     # DB connection
│   │   │   ├── security.py     # JWT & password hashing
│   │   │   └── dependencies.py # FastAPI dependencies
│   │   ├── models/             # SQLAlchemy models (29 models)
│   │   │   ├── user.py
│   │   │   ├── user_role.py
│   │   │   ├── student_profile.py
│   │   │   ├── study_plan.py
│   │   │   ├── study_session.py
│   │   │   ├── subject.py
│   │   │   ├── availability.py
│   │   │   ├── constraint.py
│   │   │   ├── exam.py
│   │   │   ├── grade.py
│   │   │   ├── notification.py
│   │   │   ├── generation_log.py
│   │   │   ├── university.py
│   │   │   ├── campus.py
│   │   │   ├── study_program.py
│   │   │   ├── course.py
│   │   │   ├── semester.py
│   │   │   ├── teaching_unit.py
│   │   │   ├── academic_track.py
│   │   │   ├── prerequisite.py
│   │   │   ├── course_prerequisite.py
│   │   │   ├── student_course_enrollment.py
│   │   │   ├── ects_progress.py
│   │   │   ├── priority_score.py
│   │   │   ├── risk_score.py
│   │   │   ├── validation_rule.py
│   │   │   ├── admin_role.py
│   │   │   ├── admin_permission.py
│   │   │   └── audit_log.py
│   │   ├── schemas/            # Pydantic schemas (20 modules)
│   │   │   ├── auth.py
│   │   │   ├── study_plan.py
│   │   │   ├── subject.py
│   │   │   ├── availability.py
│   │   │   ├── constraint.py
│   │   │   ├── exam.py
│   │   │   ├── grade.py
│   │   │   ├── enrollment.py
│   │   │   ├── ects_progress.py
│   │   │   ├── notification.py
│   │   │   ├── profile.py
│   │   │   ├── session.py
│   │   │   ├── curriculum.py
│   │   │   ├── admin.py
│   │   │   ├── import_audit.py
│   │   │   ├── ai_context.py
│   │   │   ├── academic_profile.py
│   │   │   ├── analysis.py
│   │   │   └── test_curriculum.py
│   │   ├── services/           # Business logic (30 services)
│   │   │   ├── planning_engine.py # Deterministic planner
│   │   │   ├── ai_service.py   # AI integration (Llama)
│   │   │   ├── validation_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── export_service.py # PDF generation
│   │   │   ├── study_plan_service.py
│   │   │   ├── session_edit_service.py
│   │   │   ├── background_jobs.py
│   │   │   ├── university_service.py
│   │   │   ├── program_service.py
│   │   │   ├── course_service.py
│   │   │   ├── semester_service.py
│   │   │   ├── teaching_unit_service.py
│   │   │   ├── academic_track_service.py
│   │   │   ├── prerequisite_service.py
│   │   │   ├── import_service.py # CSV/Excel import
│   │   │   ├── audit_service.py
│   │   │   ├── academic_profile_service.py
│   │   │   ├── ai_context_service.py
│   │   │   ├── ects_service.py
│   │   │   ├── exam_service.py
│   │   │   ├── grade_service.py
│   │   │   ├── enrollment_sync_service.py
│   │   │   ├── failed_course_service.py
│   │   │   ├── plan_optimizer_service.py
│   │   │   ├── priority_service.py
│   │   │   ├── risk_analysis_service.py
│   │   │   ├── super_admin_client.py
│   │   │   └── test_import_service.py
│   │   ├── middleware/         # Middleware
│   │   │   └── rbac.py         # Role-based access control
│   │   ├── tests/              # Test suite (15 test files)
│   │   │   ├── conftest.py
│   │   │   ├── test_auth.py
│   │   │   ├── test_models.py
│   │   │   ├── test_profile.py
│   │   │   ├── test_security.py
│   │   │   ├── test_audit_service.py
│   │   │   ├── test_notification_service.py
│   │   │   ├── test_validation_service.py
│   │   │   ├── test_export_service.py
│   │   │   ├── test_exports_api.py
│   │   │   ├── test_university_service.py
│   │   │   ├── test_academic_models.py
│   │   │   ├── test_audit_and_role_models.py
│   │   │   ├── test_rbac_middleware.py
│   │   │   └── test_main.py
│   │   └── main.py             # Application entry point
│   ├── scripts/                # Utility scripts
│   ├── uploads/                # File uploads storage
│   ├── requirements.txt        # Python dependencies
│   ├── alembic.ini             # Alembic configuration
│   ├── pytest.ini              # Pytest configuration
│   ├── .env.example            # Environment variables template
│   └── start_backend.bat/sh    # Startup scripts
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── ProfilePage.jsx
│   │   │   ├── SubjectsPage.jsx
│   │   │   ├── AvailabilitiesPage.jsx
│   │   │   ├── ConstraintsPage.jsx
│   │   │   ├── ExamsPage.jsx
│   │   │   ├── PlannerPage.jsx
│   │   │   ├── AIPlanPage.jsx
│   │   │   ├── ProgressionPage.jsx
│   │   │   ├── RecommendationsPage.jsx
│   │   │   ├── PreferencesPage.jsx
│   │   │   └── admin/          # Admin pages (15 pages)
│   │   │       ├── AdminDashboard.jsx
│   │   │       ├── Universities.jsx
│   │   │       ├── StudyPrograms.jsx
│   │   │       ├── Courses.jsx
│   │   │       ├── AcademicTracks.jsx
│   │   │       ├── TeachingUnits.jsx
│   │   │       ├── Semesters.jsx
│   │   │       ├── BulkImport.jsx
│   │   │       ├── ImportHistory.jsx
│   │   │       ├── ValidationRules.jsx
│   │   │       ├── AuditLogs.jsx
│   │   │       ├── RoleManagement.jsx
│   │   │       ├── Settings.jsx
│   │   │       ├── Reports.jsx
│   │   │       └── AdminPlaceholder.jsx
│   │   ├── context/            # React contexts
│   │   │   ├── AuthContext.jsx
│   │   │   ├── StudyPlanContext.jsx
│   │   │   ├── AcademicDataContext.jsx
│   │   │   ├── ThemeContext.jsx
│   │   │   ├── LanguageContext.jsx
│   │   │   └── GamificationContext.jsx
│   │   ├── api/                # API client
│   │   │   └── client.js
│   │   ├── App.jsx             # Root component
│   │   └── main.jsx            # Application entry point
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite configuration
│   ├── vitest.config.js        # Vitest configuration
│   ├── .env.example            # Environment variables template
│   └── start_frontend.bat/sh   # Startup scripts
├── notebooks/                  # Jupyter/Colab notebooks
│   ├── colab_aiplaning.ipynb   # Colab inference server
│   └── README.md               # Notebook documentation
├── ARCHITECTURE.md             # Architecture documentation
├── GOOGLE_COLAB_SETUP.md       # Colab setup guide
├── start_all.bat               # Start all services
└── README.md                   # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Google Colab account (for AI features) OR Ollama (local fallback)

### System Requirements

**Backend:**
- 2 GB RAM minimum (4 GB recommended)
- 2 CPU cores minimum
- 5 GB disk space

**Frontend:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled

**AI Service (Colab):**
- Google account
- Stable internet connection
- T4/L4/A100 GPU (provided by Colab)

**AI Service (Ollama - Local):**
- 8 GB RAM minimum (16 GB recommended for Llama 3.2 8B)
- 10 GB disk space for model
- CPU: 4+ cores (GPU optional but recommended)

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: http://localhost:8000
   API documentation: http://localhost:8000/api/docs

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://localhost:5173

### AI Service Setup

The application supports two AI service configurations:

#### Option 1: Google Colab + Llama 3.2 + LoRA (Recommended for Production)

This is the cost-effective production solution (0-50€/month).

**⚡ Quick Start (10 minutes):** See [QUICK_START_COLAB.md](./recap/QUICK_START_COLAB.md)

1. **Set up Google Colab notebook**
   - Upload `notebooks/colab_aiplaning.ipynb` to Google Colab
   - Runtime → Change runtime type → T4 GPU
   - Runtime → Run all (wait 3-5 minutes)
   - Copy the ngrok URL and API key displayed

2. **Configure backend**
   ```bash
   # In backend/.env
   AI_SERVICE_TYPE=colab
   COLAB_API_URL=https://xxxx-xx-xx.ngrok-free.app  # From Colab notebook
   COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx        # From Colab notebook
   ```

3. **Test connection**
   ```bash
   cd backend
   python test_colab_connection.py
   ```

4. **Start your backend**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

**Documentation:**
- [Quick Start Guide](./recap/QUICK_START_COLAB.md) - 10-minute setup
- [Complete Setup Guide](./GOOGLE_COLAB_SETUP.md) - Detailed instructions
- [Notebooks README](./notebooks/README.md) - Notebook documentation

**Cost Estimate:**
- Free tier: Limited GPU hours
- Colab Pro: ~10€/month for extended GPU access
- Scales to ~50 users before needing VPS migration

#### Option 2: Local Ollama (Development/Fallback)

For local development or as a fallback when Colab is unavailable.

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull Llama 3.2 model**
   ```bash
   ollama pull llama3.2
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

4. **Configure backend**
   ```bash
   # In backend/.env
   AI_SERVICE_TYPE=ollama
   AI_SERVICE_URL=http://127.0.0.1:11434
   AI_MODEL_NAME=llama3.2
   ```

   Ollama API will be available at: http://127.0.0.1:11434

**Note:** The backend automatically falls back to Ollama if the Colab service is unavailable.

## 🧪 Testing

### Backend Tests

The backend includes a comprehensive test suite with 15 test modules covering:
- Authentication and security
- Database models and relationships
- API endpoints
- Business services
- RBAC middleware
- Export functionality
- Audit logging

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run tests with verbose output
pytest -v
```

**Test Files:**
- `test_auth.py` - Authentication endpoints
- `test_models.py` - Database models
- `test_profile.py` - User profile
- `test_security.py` - Security functions
- `test_audit_service.py` - Audit logging
- `test_notification_service.py` - Notifications
- `test_validation_service.py` - Validation
- `test_export_service.py` - PDF export
- `test_exports_api.py` - Export API
- `test_university_service.py` - University service
- `test_academic_models.py` - Academic models
- `test_audit_and_role_models.py` - Audit & roles
- `test_rbac_middleware.py` - RBAC
- `test_main.py` - Main application

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm test -- --watch
```

For detailed testing guide, see [TESTING_GUIDE.md](./frontend/TESTING_GUIDE.md)

## 🔧 Development

### Code Formatting

**Backend (Python)**
```bash
cd backend
black app/
isort app/
flake8 app/
```

**Frontend (JavaScript)**
```bash
cd frontend
npm run lint
npm run format
```

### Database Migrations

**Create new migration**
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations**
```bash
alembic upgrade head
```

**Rollback migration**
```bash
alembic downgrade -1
```

**View migration history**
```bash
alembic history
```

**Current migrations (8 files):**
1. `4c065a15bc77` - Initial database schema
2. `1db0219f8f7e` - Add student course enrollments
3. `6c4ec519a8aa` - Add catalog course ID to subjects
4. `a8f2e3b4c567` - Add enhanced student fields
5. `b42401a5c708` - Add audit logging and role models
6. `c91e34f7b201` - Add admin platform performance indexes
7. `d5f8a9b2c341` - Add academic tracking tables
8. `e8a9c7f3d512` - Fix unique constraints for soft delete

### Database Schema

The application uses PostgreSQL with **29 interconnected models**:

**Core User Models:**
- `users` - User accounts
- `user_roles` - User role assignments
- `student_profiles` - Student-specific data

**Study Planning:**
- `study_plans` - Generated study plans
- `study_sessions` - Individual study sessions
- `generation_logs` - Plan generation history

**Academic Data:**
- `subjects` - Student's subjects
- `exams` - Exam schedule
- `grades` - Student grades
- `availabilities` - Time availability
- `constraints` - Planning constraints
- `notifications` - User notifications

**Institutional Data:**
- `universities` - Educational institutions
- `campuses` - University campuses
- `study_programs` - Degree programs
- `courses` - Course catalog
- `semesters` - Academic semesters
- `teaching_units` - Course units
- `academic_tracks` - Specialization tracks
- `prerequisites` - Course prerequisites
- `course_prerequisites` - Course dependency mapping

**Progress Tracking:**
- `student_course_enrollments` - Course enrollments
- `ects_progress` - ECTS credit tracking
- `priority_scores` - Subject priority scores
- `risk_scores` - Academic risk assessment

**Administration:**
- `admin_roles` - Admin role definitions
- `admin_permissions` - Permission definitions
- `audit_logs` - Audit trail
- `validation_rules` - Custom validation logic

For complete schema documentation, see [backend/DATABASE_SCHEMA.md](./backend/DATABASE_SCHEMA.md)

---

## 🔧 Backend Services Architecture

The backend includes **30+ specialized services** organized by domain:

### Core Planning Services
- **`planning_engine.py`** - Deterministic planning algorithm
  - Analyzes student availability and constraints
  - Calculates optimal time slots
  - Balances workload across the week
  - Ensures prerequisite satisfaction

- **`ai_service.py`** - AI integration (Llama 3.2)
  - Connects to Colab or Ollama
  - Builds contextual prompts
  - Processes AI responses
  - Handles fallback strategies
  - Documentation: [COLAB_INTEGRATION.md](./backend/app/services/COLAB_INTEGRATION.md)

- **`validation_service.py`** - Plan validation
  - Schema validation
  - Constraint checking
  - Conflict detection
  - Auto-correction
  - Documentation: [VALIDATION_SERVICE_README.md](./backend/app/services/VALIDATION_SERVICE_README.md)

### Student Services
- **`study_plan_service.py`** - Study plan CRUD operations
- **`session_edit_service.py`** - Study session editing
- **`academic_profile_service.py`** - Academic profiling
- **`ai_context_service.py`** - AI context building
- **`ects_service.py`** - ECTS progress tracking
- **`exam_service.py`** - Exam management
- **`grade_service.py`** - Grade management
- **`enrollment_sync_service.py`** - Course enrollment sync

### Analysis Services
- **`plan_optimizer_service.py`** - Plan optimization
- **`priority_service.py`** - Subject prioritization
- **`risk_analysis_service.py`** - Academic risk assessment
- **`failed_course_service.py`** - Failed course tracking

### Institutional Services
- **`university_service.py`** - University management
- **`program_service.py`** - Study program management
- **`course_service.py`** - Course catalog management
- **`semester_service.py`** - Semester management
- **`teaching_unit_service.py`** - Teaching unit management
- **`academic_track_service.py`** - Academic track management
- **`prerequisite_service.py`** - Prerequisite management

### Administrative Services
- **`import_service.py`** - Bulk CSV/Excel import
  - Documentation: [IMPORT_SERVICE_README.md](./backend/app/services/IMPORT_SERVICE_README.md)
- **`audit_service.py`** - Audit logging
  - Documentation: [AUDIT_SERVICE_README.md](./backend/app/services/AUDIT_SERVICE_README.md)
- **`super_admin_client.py`** - Super admin operations

### Utility Services
- **`notification_service.py`** - Notification system
- **`export_service.py`** - PDF export with ReportLab
- **`background_jobs.py`** - Async background tasks

---

## 📦 Deployment

### Manual Deployment

The application uses a manual deployment approach with separate backend and frontend servers.

**Backend (FastAPI):**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend (React):**
```bash
cd frontend
npm run build
npm run preview  # Or use a static server like nginx
```

**Note:** Docker containerization is planned for future releases.

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Main API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

#### Study Planning
- `GET /api/v1/study-plans` - List study plans
- `POST /api/v1/study-plans/generate` - Generate new plan
- `GET /api/v1/study-plans/{id}` - Get plan details
- `PUT /api/v1/study-plans/{id}` - Update plan
- `DELETE /api/v1/study-plans/{id}` - Delete plan
- `GET /api/v1/study-plans/{id}/export` - Export plan to PDF

#### Subject Management
- `GET /api/v1/subjects` - List subjects
- `POST /api/v1/subjects` - Create subject
- `PUT /api/v1/subjects/{id}` - Update subject
- `DELETE /api/v1/subjects/{id}` - Delete subject

#### Availability & Constraints
- `GET /api/v1/availabilities` - List availabilities
- `POST /api/v1/availabilities` - Create availability
- `GET /api/v1/constraints` - List constraints
- `POST /api/v1/constraints` - Create constraint

#### Academic Data
- `GET /api/v1/exams` - List exams
- `POST /api/v1/exams` - Create exam
- `GET /api/v1/grades` - List grades
- `POST /api/v1/grades` - Record grade
- `GET /api/v1/enrollments` - List course enrollments
- `GET /api/v1/ects` - ECTS progress tracking

#### AI & Analysis
- `POST /api/v1/ai-context` - Build AI context
- `GET /api/v1/academic-profile` - Get academic profile
- `POST /api/v1/analysis` - Analyze academic performance
- `POST /api/v1/plan-optimizer` - Optimize study plan
- `POST /api/v1/chat` - AI chat interface

#### Notifications
- `GET /api/v1/notifications` - List notifications
- `PUT /api/v1/notifications/{id}/read` - Mark as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

#### Administration (RBAC Protected)
- `GET /api/v1/admin/dashboard` - Admin dashboard stats
- `GET /api/v1/admin/universities` - List universities
- `POST /api/v1/admin/universities` - Create university
- `GET /api/v1/admin/study-programs` - List study programs
- `POST /api/v1/admin/study-programs` - Create program
- `GET /api/v1/admin/courses` - List courses
- `POST /api/v1/admin/courses` - Create course
- `GET /api/v1/admin/academic-tracks` - List academic tracks
- `GET /api/v1/admin/teaching-units` - List teaching units
- `GET /api/v1/admin/semesters` - List semesters
- `GET /api/v1/admin/prerequisites` - List prerequisites
- `GET /api/v1/admin/validation-rules` - List validation rules
- `POST /api/v1/admin/imports` - Bulk import (CSV/Excel)
- `GET /api/v1/admin/exports` - Export data
- `GET /api/v1/admin/search` - Global admin search
- `GET /api/v1/admin/audit` - Audit logs
- `GET /api/v1/admin/roles` - Role management
- `GET /api/v1/admin/settings` - System settings

For complete API documentation with request/response schemas, visit the Swagger UI.

---

## 🏢 Super Admin Platform

AI Study Planner includes a complete institutional management platform for universities and educational institutions.

### Key Features

**📚 Academic Management**
- **Universities & Campuses**: Multi-institution support with hierarchical structure
- **Study Programs**: Bachelor, Master, Doctorate programs management
- **Academic Tracks**: Specialization paths within programs
- **Courses Catalog**: Complete course management with ECTS credits
- **Teaching Units**: Modular course groupings
- **Semesters**: Academic calendar management
- **Prerequisites**: Course dependency management
- **Validation Rules**: Custom validation logic

**📥 Data Management**
- **Bulk Import**: CSV/Excel import for courses, students, programs
- **Import History**: Track all import operations with detailed logs
- **Data Export**: Export institutional data in multiple formats
- **Global Search**: Search across all entities (courses, students, programs)

**👥 User & Role Management**
- **RBAC**: Role-Based Access Control (Student, Admin, Super Admin)
- **Role Management**: Create and manage custom roles with granular permissions
- **Permission System**: Fine-grained access control to features and data

**📊 Monitoring & Analytics**
- **Admin Dashboard**: Real-time statistics and KPIs
- **Audit Logging**: Complete audit trail of all administrative actions
- **Reports**: Generate institutional reports and analytics
- **System Settings**: Configure platform-wide settings

### Access Requirements

To access the Super Admin Platform, you need:
1. A user account with **Admin** or **Super Admin** role
2. Appropriate permissions assigned to your role
3. Navigate to `/admin` routes in the frontend

### Admin Routes

| Route | Description |
|-------|-------------|
| `/admin/dashboard` | Overview of institutional data and statistics |
| `/admin/universities` | Manage universities and institutions |
| `/admin/study-programs` | Manage study programs (Bachelor, Master, etc.) |
| `/admin/courses` | Manage course catalog |
| `/admin/academic-tracks` | Manage specialization tracks |
| `/admin/teaching-units` | Manage teaching units |
| `/admin/semesters` | Manage academic semesters |
| `/admin/bulk-import` | Import data from CSV/Excel files |
| `/admin/import-history` | View import operation history |
| `/admin/validation-rules` | Configure validation rules |
| `/admin/audit-logs` | View complete audit trail |
| `/admin/roles` | Manage user roles and permissions |
| `/admin/settings` | System configuration |
| `/admin/reports` | Generate institutional reports |

### Bulk Import Format

The platform supports CSV/Excel import for:
- **Courses**: `course_code`, `name`, `ects_credits`, `semester`, `is_mandatory`
- **Students**: `email`, `full_name`, `program_id`, `semester`
- **Programs**: `name`, `code`, `degree_level`, `duration_semesters`

Example CSV format:
```csv
course_code,name,ects_credits,semester,is_mandatory
CS101,Introduction to Programming,6,1,true
MATH201,Linear Algebra,5,2,true
```

For detailed import guide, see [backend/app/services/IMPORT_SERVICE_README.md](./backend/app/services/IMPORT_SERVICE_README.md)

### Audit Logging

All administrative actions are logged with:
- **User**: Who performed the action
- **Action**: What was done (create, update, delete)
- **Entity**: What was affected (course, user, program)
- **Timestamp**: When it happened
- **IP Address**: Where it came from
- **Changes**: Before/after values for updates

View audit logs in `/admin/audit-logs` or via API:
```bash
GET /api/v1/admin/audit?user_id=123&entity_type=course&limit=50
```

For detailed audit service documentation, see [backend/app/services/AUDIT_SERVICE_README.md](./backend/app/services/AUDIT_SERVICE_README.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🛠️ Utility Scripts

The project includes several utility scripts for development and maintenance:

### Backend Scripts

**Database Management:**
- `create_database.py` - Create PostgreSQL database
- `create_db_sqlalchemy.py` - Create database via SQLAlchemy
- `cleanup_old_plans.py` - Clean up old study plans

**Testing:**
- `test_colab_quick.py` - Quick Colab connection test
- `test_colab_simple.py` - Simple Colab API test
- `debug_auth.py` - Debug authentication issues

**Batch Files (Windows):**
- `start_backend.bat` - Start FastAPI server
- `start_ollama.bat` - Start Ollama service
- `stop_postgres18.bat` - Stop PostgreSQL service
- `create_db.bat` - Create database
- `apply_migration.bat` - Apply Alembic migrations

**Shell Scripts (Unix/Linux/macOS):**
- `start_backend.sh` - Start FastAPI server

### Frontend Scripts

**Batch Files (Windows):**
- `start_frontend.bat` - Start React dev server

**Shell Scripts (Unix/Linux/macOS):**
- `start_frontend.sh` - Start React dev server

### Project-Wide Scripts

- `start_all.bat` - Start backend, frontend, and all services (Windows)

---

## 📚 Additional Documentation

The project includes extensive inline documentation:

**Backend Documentation:**
- [DATABASE_SCHEMA.md](./backend/DATABASE_SCHEMA.md) - Complete database schema
- [AUDIT_SERVICE_README.md](./backend/app/services/AUDIT_SERVICE_README.md) - Audit logging guide
- [IMPORT_SERVICE_README.md](./backend/app/services/IMPORT_SERVICE_README.md) - Bulk import guide
- [VALIDATION_SERVICE_README.md](./backend/app/services/VALIDATION_SERVICE_README.md) - Validation guide
- [COLAB_INTEGRATION.md](./backend/app/services/COLAB_INTEGRATION.md) - Colab integration details
- [IMPORT_AUDIT_SCHEMAS_README.md](./backend/app/schemas/IMPORT_AUDIT_SCHEMAS_README.md) - Import schemas

**Frontend Documentation:**
- [TESTING_GUIDE.md](./frontend/TESTING_GUIDE.md) - Frontend testing guide

**Project Documentation:**
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed architecture documentation
- [GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md) - Complete Colab setup guide
- [recap/QUICK_START_COLAB.md](./recap/QUICK_START_COLAB.md) - 10-minute Colab quickstart
- [recap/ARCHITECTURE_DECISIONS.md](./recap/ARCHITECTURE_DECISIONS.md) - Architecture decision records

**Task Completion Summaries:**
- [TASK_2.3_COMPLETION_SUMMARY.md](./backend/TASK_2.3_COMPLETION_SUMMARY.md)
- [TASK_3.2_COMPLETION_SUMMARY.md](./backend/TASK_3.2_COMPLETION_SUMMARY.md)
- [TASK_5.3_COMPLETION_SUMMARY.md](./backend/TASK_5.3_COMPLETION_SUMMARY.md)
- [SEMESTER_ENDPOINTS_IMPLEMENTATION.md](./backend/SEMESTER_ENDPOINTS_IMPLEMENTATION.md)

---

## 📄 License

This project is part of an academic Bachelor/Master program.

## 👥 Team

- Backend Development: Python/FastAPI
- Frontend Development: React/TypeScript
- DevOps: Docker/Nginx

## 📞 Support

For questions or issues, please open an issue on GitHub.

---

**Version**: 1.0.0  
**Last Updated**: May 2026
