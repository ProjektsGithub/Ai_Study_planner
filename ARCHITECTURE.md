# 🏗️ Architecture du Projet AI Study Planner

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Globale](#architecture-globale)
3. [Stack Technique](#stack-technique)
4. [Structure du Projet](#structure-du-projet)
5. [Architecture Backend](#architecture-backend)
6. [Architecture Frontend](#architecture-frontend)
7. [Architecture Base de Données](#architecture-base-de-données)
8. [Architecture IA](#architecture-ia)
9. [Flux de Données](#flux-de-données)
10. [Sécurité](#sécurité)
11. [Déploiement](#déploiement)

---

## 🎯 Vue d'ensemble

**AI Study Planner** est une application web full-stack intelligente qui génère automatiquement des plannings d'études hebdomadaires personnalisés pour les étudiants universitaires.

### Caractéristiques Principales

- ✅ Génération automatique de plannings d'études équilibrés
- 🎯 Priorisation intelligente basée sur l'IA
- ✏️ Édition manuelle des plannings générés
- 📊 Suivi de progression académique
- 📄 Export PDF des plannings
- 🔔 Système de notifications
- 👥 Gestion multi-utilisateurs avec RBAC
- 🏢 Plateforme super-admin pour institutions

---

## 🏛️ Architecture Globale

### Schéma de l'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React Application (Frontend)                            │  │
│  │  • React 19.2.6 + React Router                          │  │
│  │  • Ant Design 6.4.4 + Tailwind CSS 3.4.1              │  │
│  │  • TanStack Query 5.101.0                             │  │
│  │  • Axios pour HTTP                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python 3.11+)                         │  │
│  │  • RESTful API                                           │  │
│  │  • JWT Authentication                                    │  │
│  │  • RBAC Middleware                                       │  │
│  │  • CORS & Security Headers                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       BUSINESS LOGIC LAYER                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services Layer                                          │  │
│  │  • Planning Engine (Déterministe)                       │  │
│  │  • AI Service (Llama 3.2 + LoRA)                       │  │
│  │  • Validation Service                                    │  │
│  │  • Notification Service                                  │  │
│  │  • Export Service (PDF)                                  │  │
│  │  • Audit Service                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 15+                                          │  │
│  │  • SQLAlchemy ORM                                        │  │
│  │  • Alembic Migrations                                    │  │
│  │  • 30+ Tables                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         AI SERVICE LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Option 1: Google Colab (Production)                    │  │
│  │  • Llama 3.2 + LoRA Fine-tuning                         │  │
│  │  • GPU T4/A100                                           │  │
│  │  • ngrok Tunnel                                          │  │
│  │  • Coût: 0-50€/mois                                     │  │
│  │                                                           │  │
│  │  Option 2: Ollama (Dev/Fallback)                        │  │
│  │  • Llama 3.2 Local                                       │  │
│  │  • CPU/GPU Local                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Technique

### Backend Stack

| Composant | Technologie | Version | Usage |
|-----------|-------------|---------|--------|
| **Framework** | FastAPI | 0.109.0 | API REST principal |
| **Serveur ASGI** | Uvicorn | 0.27.0 | Serveur d'application |
| **ORM** | SQLAlchemy | 2.0.25 | Mapping objet-relationnel |
| **Migrations** | Alembic | 1.13.1 | Gestion schéma DB |
| **Base de données** | PostgreSQL | 15+ | Stockage de données |
| **Driver DB** | psycopg2-binary | 2.9.9 | Connecteur PostgreSQL |
| **Validation** | Pydantic | 2.5.3 | Validation de données |
| **Authentification** | python-jose | 3.3.0 | JWT tokens |
| **Hash Passwords** | passlib[argon2] | 1.7.4 | Sécurité des mots de passe |
| **HTTP Client** | httpx | 0.26.0 | Appels API externes |
| **PDF Generation** | reportlab | 4.0.9 | Export PDF |
| **Testing** | pytest | 7.4.4 | Tests unitaires |
| **Code Quality** | black, isort, flake8 | latest | Formatage et linting |

### Frontend Stack

| Composant | Technologie | Version | Usage |
|-----------|-------------|---------|--------|
| **Framework** | React | 19.2.6 | UI Framework |
| **Build Tool** | Vite | 8.0.12 | Bundler & Dev Server |
| **Routing** | React Router | 7.15.1 | Navigation SPA |
| **State Management** | TanStack Query | 5.101.0 | Server state & cache |
| **UI Library** | Ant Design | 6.4.4 | Composants UI |
| **Styling** | Tailwind CSS | 3.4.1 | Utility-first CSS |
| **Icons** | Ant Design Icons | 6.2.5 | Bibliothèque d'icônes |
| **HTTP Client** | Axios | 1.16.1 | Requêtes HTTP |
| **Testing** | Vitest | 4.1.7 | Tests unitaires |
| **Testing Library** | @testing-library/react | 16.3.2 | Tests composants |

### IA & ML Stack

| Composant | Technologie | Usage |
|-----------|-------------|--------|
| **Modèle Base** | Llama 3.2 | Modèle de langage |
| **Fine-tuning** | LoRA (Low-Rank Adaptation) | Adaptation du modèle |
| **Hébergement Production** | Google Colab | GPU T4/A100, ngrok tunnel |
| **Alternative Locale** | Ollama | Développement et fallback |
| **Bibliothèques ML** | Unsloth, transformers | Optimisation et entraînement |

---

## 📁 Structure du Projet

### Arborescence Complète

```
AIplaning/
│
├── 📂 backend/                      # Backend FastAPI
│   ├── 📂 alembic/                 # Migrations de base de données
│   │   ├── versions/               # Scripts de migration
│   │   ├── env.py                  # Configuration Alembic
│   │   └── script.py.mako          # Template de migration
│   │
│   ├── 📂 app/                     # Application principale
│   │   ├── 📂 api/                 # Couche API
│   │   │   └── 📂 v1/              # API Version 1
│   │   │       ├── __init__.py
│   │   │       ├── auth.py         # Authentification endpoints
│   │   │       ├── study_plans.py  # Plannings endpoints
│   │   │       ├── subjects.py     # Matières endpoints
│   │   │       ├── availabilities.py
│   │   │       ├── constraints.py
│   │   │       ├── exams.py
│   │   │       ├── grades.py
│   │   │       ├── enrollments.py
│   │   │       ├── profile.py
│   │   │       ├── notifications.py
│   │   │       ├── exports.py
│   │   │       ├── analysis.py
│   │   │       ├── plan_optimizer.py
│   │   │       ├── ai_context.py
│   │   │       ├── academic_profile.py
│   │   │       ├── ects.py
│   │   │       └── 📂 admin/       # Administration endpoints
│   │   │           ├── universities.py
│   │   │           ├── campuses.py
│   │   │           ├── programs.py
│   │   │           ├── courses.py
│   │   │           ├── semesters.py
│   │   │           ├── students.py
│   │   │           ├── teaching_units.py
│   │   │           ├── audit.py
│   │   │           └── roles.py
│   │   │
│   │   ├── 📂 core/                # Configuration & Core
│   │   │   ├── config.py           # Configuration app
│   │   │   ├── database.py         # Connexion DB
│   │   │   ├── security.py         # JWT & hashing
│   │   │   └── dependencies.py     # Dépendances FastAPI
│   │   │
│   │   ├── 📂 models/              # Modèles SQLAlchemy (30+ modèles)
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # Utilisateur
│   │   │   ├── student_profile.py  # Profil étudiant
│   │   │   ├── study_plan.py       # Plan d'études
│   │   │   ├── study_session.py    # Session d'étude
│   │   │   ├── subject.py          # Matière
│   │   │   ├── availability.py     # Disponibilité
│   │   │   ├── constraint.py       # Contrainte
│   │   │   ├── exam.py             # Examen
│   │   │   ├── grade.py            # Note
│   │   │   ├── notification.py     # Notification
│   │   │   ├── generation_log.py   # Log génération
│   │   │   ├── university.py       # Université
│   │   │   ├── campus.py           # Campus
│   │   │   ├── study_program.py    # Programme d'études
│   │   │   ├── course.py           # Cours
│   │   │   ├── semester.py         # Semestre
│   │   │   ├── teaching_unit.py    # Unité d'enseignement
│   │   │   ├── academic_track.py   # Parcours académique
│   │   │   ├── prerequisite.py     # Prérequis
│   │   │   ├── course_prerequisite.py
│   │   │   ├── student_course_enrollment.py
│   │   │   ├── ects_progress.py    # Progression ECTS
│   │   │   ├── priority_score.py   # Score de priorité
│   │   │   ├── risk_score.py       # Score de risque
│   │   │   ├── validation_rule.py  # Règle de validation
│   │   │   ├── admin_role.py       # Rôle administrateur
│   │   │   ├── admin_permission.py # Permission admin
│   │   │   ├── user_role.py        # Rôle utilisateur
│   │   │   └── audit_log.py        # Journal d'audit
│   │   │
│   │   ├── 📂 schemas/             # Schémas Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Schémas authentification
│   │   │   ├── study_plan.py       # Schémas planning
│   │   │   ├── subject.py          # Schémas matière
│   │   │   ├── availability.py
│   │   │   ├── constraint.py
│   │   │   ├── exam.py
│   │   │   ├── grade.py
│   │   │   ├── enrollment.py
│   │   │   ├── notification.py
│   │   │   ├── profile.py
│   │   │   ├── session.py
│   │   │   ├── curriculum.py
│   │   │   ├── admin.py
│   │   │   ├── import_audit.py
│   │   │   ├── ai_context.py
│   │   │   ├── academic_profile.py
│   │   │   ├── analysis.py
│   │   │   └── ects_progress.py
│   │   │
│   │   ├── 📂 services/            # Logique métier (20+ services)
│   │   │   ├── __init__.py
│   │   │   ├── planning_engine.py  # Moteur de planification
│   │   │   ├── ai_service.py       # Service IA (Llama)
│   │   │   ├── validation_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── export_service.py   # Export PDF
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
│   │   │   ├── import_service.py
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
│   │   │   └── super_admin_client.py
│   │   │
│   │   ├── 📂 middleware/          # Middlewares
│   │   │   ├── __init__.py
│   │   │   └── rbac.py             # Role-Based Access Control
│   │   │
│   │   ├── 📂 tests/               # Tests unitaires
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
│   │   │
│   │   └── main.py                 # Point d'entrée FastAPI
│   │
│   ├── 📂 scripts/                 # Scripts utilitaires
│   ├── 📂 tests/                   # Tests d'intégration
│   ├── 📂 uploads/                 # Fichiers uploadés
│   ├── requirements.txt            # Dépendances Python
│   ├── .env.example                # Variables d'environnement
│   ├── alembic.ini                 # Configuration Alembic
│   ├── pytest.ini                  # Configuration pytest
│   └── pyproject.toml              # Configuration projet Python
│
├── 📂 frontend/                     # Frontend React
│   ├── 📂 public/                  # Assets statiques
│   │
│   ├── 📂 src/                     # Code source
│   │   ├── 📂 api/                 # Client API
│   │   │   └── client.js           # Axios client configuré
│   │   │
│   │   ├── 📂 components/          # Composants React
│   │   │   ├── 📂 layout/          # Composants de mise en page
│   │   │   ├── 📂 dashboard/       # Composants tableau de bord
│   │   │   ├── 📂 subjects/        # Composants matières
│   │   │   ├── 📂 exams/           # Composants examens
│   │   │   ├── 📂 progression/     # Composants progression
│   │   │   ├── 📂 recommendations/ # Composants recommandations
│   │   │   ├── 📂 gamification/    # Composants gamification
│   │   │   ├── 📂 ui/              # Composants UI réutilisables
│   │   │   ├── WeeklyCalendarView.jsx    # Calendrier hebdo
│   │   │   ├── SessionEditor.jsx        # Éditeur de session
│   │   │   ├── SubjectManager.jsx       # Gestionnaire matières
│   │   │   ├── AvailabilityManager.jsx  # Gestionnaire dispo
│   │   │   ├── ConstraintManager.jsx    # Gestionnaire contraintes
│   │   │   ├── NotificationPanel.jsx    # Panneau notifications
│   │   │   ├── ErrorBoundary.jsx        # Gestion erreurs
│   │   │   ├── ErrorDisplay.jsx
│   │   │   ├── EntityHistory.jsx
│   │   │   ├── GlobalSearch.jsx
│   │   │   ├── ProtectedRoute.jsx       # Route protégée
│   │   │   └── HomeRedirect.jsx
│   │   │
│   │   ├── 📂 context/             # Contexts React
│   │   │   ├── AuthContext.jsx     # Contexte authentification
│   │   │   ├── StudyPlanContext.jsx # Contexte planning
│   │   │   ├── AcademicDataContext.jsx
│   │   │   ├── ThemeContext.jsx    # Contexte thème
│   │   │   ├── LanguageContext.jsx # Contexte langue
│   │   │   └── GamificationContext.jsx
│   │   │
│   │   ├── 📂 pages/               # Pages de l'application
│   │   │   ├── 📂 admin/           # Pages administration
│   │   │   │   ├── UniversitiesPage.jsx
│   │   │   │   ├── CampusesPage.jsx
│   │   │   │   ├── ProgramsPage.jsx
│   │   │   │   ├── CoursesPage.jsx
│   │   │   │   ├── SemestersPage.jsx
│   │   │   │   ├── StudentsPage.jsx
│   │   │   │   ├── TeachingUnitsPage.jsx
│   │   │   │   ├── AuditLogPage.jsx
│   │   │   │   └── RolesPage.jsx
│   │   │   ├── LoginPage.jsx       # Page connexion
│   │   │   ├── RegisterPage.jsx    # Page inscription
│   │   │   ├── DashboardPage.jsx   # Tableau de bord
│   │   │   ├── ProfilePage.jsx     # Profil utilisateur
│   │   │   ├── SubjectsPage.jsx    # Gestion matières
│   │   │   ├── AvailabilitiesPage.jsx
│   │   │   ├── ConstraintsPage.jsx
│   │   │   ├── ExamsPage.jsx
│   │   │   ├── PlannerPage.jsx     # Générateur de planning
│   │   │   ├── AIPlanPage.jsx      # Planning IA
│   │   │   ├── CalendarDemo.jsx
│   │   │   ├── ProgressionPage.jsx
│   │   │   ├── RecommendationsPage.jsx
│   │   │   ├── PreferencesPage.jsx
│   │   │   ├── NotFoundPage.jsx
│   │   │   └── UnauthorizedPage.jsx
│   │   │
│   │   ├── 📂 test/                # Configuration tests
│   │   │   └── setup.js
│   │   │
│   │   ├── App.jsx                 # Composant racine
│   │   ├── main.jsx                # Point d'entrée
│   │   └── index.css               # Styles globaux
│   │
│   ├── package.json                # Dépendances Node.js
│   ├── vite.config.js              # Configuration Vite
│   ├── vitest.config.js            # Configuration Vitest
│   ├── tailwind.config.js          # Configuration Tailwind
│   ├── postcss.config.js           # Configuration PostCSS
│   ├── .env.example                # Variables d'environnement
│   └── index.html                  # HTML racine
│
├── 📂 notebooks/                    # Notebooks Jupyter/Colab
│   ├── colab_inference_server.ipynb # Serveur IA Colab
│   └── README.md
│
├── 📂 charts/                       # Graphiques & visualisations
│
├── 📂 recap/                        # Documentation projet
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── PROJECT_REFERENCE.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   └── ...
│
├── README.md                        # Documentation principale
├── ARCHITECTURE.md                  # Ce document
├── GOOGLE_COLAB_SETUP.md           # Guide setup Colab
├── .gitignore                       # Git ignore rules
└── start_all.bat                    # Script démarrage complet
```

---

## 🔧 Architecture Backend

### Couches du Backend

```
┌─────────────────────────────────────────────────┐
│              API LAYER (FastAPI)                │
│  • Endpoints REST                               │
│  • Validation des requêtes (Pydantic)          │
│  • Documentation automatique (Swagger)          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           MIDDLEWARE LAYER                      │
│  • CORS Middleware                              │
│  • RBAC Middleware (Role-Based Access Control) │
│  • JWT Authentication                           │
│  • Request Logging                              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│            SERVICES LAYER                       │
│  • Planning Engine (Déterministe)              │
│  • AI Service (Llama 3.2)                      │
│  • Validation Service                           │
│  • Notification Service                         │
│  • Export Service (PDF)                         │
│  • University Service                           │
│  • Program Service                              │
│  • Course Service                               │
│  • Audit Service                                │
│  • Import Service                               │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│             ORM LAYER (SQLAlchemy)              │
│  • 30+ modèles de données                      │
│  • Relations complexes                          │
│  • Soft delete                                  │
│  • Timestamps automatiques                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          DATABASE LAYER (PostgreSQL)            │
│  • Transactions ACID                            │
│  • Indexes optimisés                            │
│  • Constraints & Relations                      │
└─────────────────────────────────────────────────┘
```

### Principaux Services Backend

#### 1. **Planning Engine** (`planning_engine.py`)
Moteur déterministe de génération de plannings :
- Analyse des disponibilités de l'étudiant
- Calcul des priorités des matières
- Construction des créneaux de temps valides
- Équilibrage de la charge de travail
- Respect des contraintes

#### 2. **AI Service** (`ai_service.py`)
Service d'intelligence artificielle :
- Appel au modèle Llama 3.2 (Colab ou Ollama)
- Construction du contexte pour l'IA
- Optimisation des prompts
- Gestion du fallback
- Retry logic avec exponential backoff

#### 3. **Validation Service** (`validation_service.py`)
Validation et auto-correction :
- Validation de schéma
- Vérification des contraintes
- Auto-correction des conflits
- Génération de warnings

#### 4. **Notification Service** (`notification_service.py`)
Système de notifications :
- Notifications en temps réel
- Email (optionnel)
- Notifications push (futur)
- Rappels d'examens
- Alertes de conflits

#### 5. **Export Service** (`export_service.py`)
Génération de documents :
- Export PDF avec ReportLab
- Formatage personnalisé
- Templates professionnels
- Graphiques et statistiques

#### 6. **University Service** (`university_service.py`)
Gestion des institutions :
- CRUD universités
- Gestion des campus
- Gestion des programmes
- Import en masse

#### 7. **Audit Service** (`audit_service.py`)
Traçabilité et logs :
- Log de toutes les actions
- Traçabilité des modifications
- Historique complet
- Conformité RGPD

### API Endpoints Principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| **Authentification** |
| `/api/v1/auth/register` | POST | Inscription utilisateur |
| `/api/v1/auth/login` | POST | Connexion |
| `/api/v1/auth/refresh` | POST | Rafraîchir token |
| **Profil** |
| `/api/v1/profile/me` | GET | Profil utilisateur |
| `/api/v1/profile/me` | PUT | Modifier profil |
| **Matières** |
| `/api/v1/subjects` | GET | Liste matières |
| `/api/v1/subjects` | POST | Créer matière |
| `/api/v1/subjects/{id}` | PUT | Modifier matière |
| `/api/v1/subjects/{id}` | DELETE | Supprimer matière |
| **Plannings** |
| `/api/v1/study-plans` | GET | Liste plannings |
| `/api/v1/study-plans/generate` | POST | Générer planning |
| `/api/v1/study-plans/{id}` | GET | Détails planning |
| `/api/v1/study-plans/{id}` | PUT | Modifier planning |
| `/api/v1/study-plans/{id}/export` | GET | Export PDF |
| **Disponibilités** |
| `/api/v1/availabilities` | GET | Liste disponibilités |
| `/api/v1/availabilities` | POST | Ajouter disponibilité |
| **Examens** |
| `/api/v1/exams` | GET | Liste examens |
| `/api/v1/exams` | POST | Créer examen |
| **Notifications** |
| `/api/v1/notifications` | GET | Liste notifications |
| `/api/v1/notifications/{id}/read` | PUT | Marquer comme lu |
| **Administration** |
| `/api/v1/admin/universities` | GET/POST | Gestion universités |
| `/api/v1/admin/campuses` | GET/POST | Gestion campus |
| `/api/v1/admin/programs` | GET/POST | Gestion programmes |
| `/api/v1/admin/courses` | GET/POST | Gestion cours |
| `/api/v1/admin/audit` | GET | Logs d'audit |

---

## 🎨 Architecture Frontend

### Structure des Composants React

```
App (Root)
│
├── Router (React Router)
│   │
│   ├── Public Routes
│   │   ├── LoginPage
│   │   ├── RegisterPage
│   │   ├── NotFoundPage
│   │   └── UnauthorizedPage
│   │
│   ├── Protected Routes (RequireAuth)
│   │   │
│   │   ├── Layout (Header + Sidebar + Content)
│   │   │   │
│   │   │   ├── DashboardPage
│   │   │   │   ├── StatsCard
│   │   │   │   ├── ProgressChart
│   │   │   │   └── UpcomingExams
│   │   │   │
│   │   │   ├── ProfilePage
│   │   │   │   ├── ProfileForm
│   │   │   │   ├── AcademicInfo
│   │   │   │   └── Preferences
│   │   │   │
│   │   │   ├── SubjectsPage
│   │   │   │   └── SubjectManager
│   │   │   │       ├── SubjectList
│   │   │   │       ├── SubjectForm
│   │   │   │       └── SubjectCard
│   │   │   │
│   │   │   ├── AvailabilitiesPage
│   │   │   │   └── AvailabilityManager
│   │   │   │       ├── TimeSlotGrid
│   │   │   │       └── AvailabilityForm
│   │   │   │
│   │   │   ├── ExamsPage
│   │   │   │   ├── ExamList
│   │   │   │   ├── ExamForm
│   │   │   │   └── ExamCalendar
│   │   │   │
│   │   │   ├── PlannerPage
│   │   │   │   ├── GenerateForm
│   │   │   │   ├── PlanHistory
│   │   │   │   └── PlanPreview
│   │   │   │
│   │   │   ├── AIPlanPage
│   │   │   │   ├── WeeklyCalendarView
│   │   │   │   ├── SessionEditor
│   │   │   │   ├── PlanActions
│   │   │   │   └── ValidationPanel
│   │   │   │
│   │   │   └── Admin Routes (RBAC)
│   │   │       ├── UniversitiesPage
│   │   │       ├── CampusesPage
│   │   │       ├── ProgramsPage
│   │   │       └── AuditLogPage
│   │   │
│   │   └── Common Components
│   │       ├── NotificationPanel
│   │       ├── GlobalSearch
│   │       ├── ErrorBoundary
│   │       └── LoadingSpinner
│   │
│   └── Contexts
│       ├── AuthContext (JWT, user state)
│       ├── StudyPlanContext (planning state)
│       ├── AcademicDataContext (données académiques)
│       ├── ThemeContext (dark/light mode)
│       ├── LanguageContext (i18n)
│       └── GamificationContext (badges, XP)
```

### Gestion d'État

#### 1. **React Context API**
- `AuthContext` : État d'authentification
- `StudyPlanContext` : État du planning actuel
- `AcademicDataContext` : Données académiques partagées
- `ThemeContext` : Thème de l'application
- `LanguageContext` : Langue de l'interface

#### 2. **TanStack Query (React Query)**
- Cache automatique des données serveur
- Refetch automatique
- Mutations optimistes
- Invalidation intelligente
- Background sync

### Routing

```javascript
// Routes publiques
/ → LoginPage
/register → RegisterPage

// Routes protégées
/dashboard → DashboardPage
/profile → ProfilePage
/subjects → SubjectsPage
/availabilities → AvailabilitiesPage
/constraints → ConstraintsPage
/exams → ExamsPage
/planner → PlannerPage
/plan/:id → AIPlanPage

// Routes admin (RBAC)
/admin/universities → UniversitiesPage
/admin/campuses → CampusesPage
/admin/programs → ProgramsPage
/admin/courses → CoursesPage
/admin/students → StudentsPage
/admin/audit → AuditLogPage

// Routes erreur
/unauthorized → UnauthorizedPage
* → NotFoundPage
```

---

## 🗄️ Architecture Base de Données

### Schéma de Base de Données (PostgreSQL)

#### Entités Principales (30+ tables)

**1. Utilisateurs & Authentification**
```
users
├── id (PK)
├── email (unique)
├── hashed_password
├── full_name
├── is_active
├── created_at
└── updated_at

user_roles
├── id (PK)
├── user_id (FK → users)
├── role (enum: student, admin, super_admin)
└── created_at
```

**2. Profils Étudiants**
```
student_profiles
├── id (PK)
├── user_id (FK → users, unique)
├── study_program_id (FK → study_programs)
├── campus_id (FK → campuses)
├── academic_track_id (FK → academic_tracks)
├── current_semester
├── total_ects
├── completed_ects
├── study_pace (enum: full_time, part_time)
├── preferred_study_times (JSONB)
├── learning_style (enum)
├── academic_goals (TEXT)
├── created_at
└── updated_at
```

**3. Institutions Académiques**
```
universities
├── id (PK)
├── name (unique)
├── code (unique)
├── country
├── city
├── is_active
└── created_at

campuses
├── id (PK)
├── university_id (FK → universities)
├── name
├── city
├── address
└── is_active

study_programs
├── id (PK)
├── campus_id (FK → campuses)
├── name
├── code (unique)
├── degree_level (enum: bachelor, master, doctorate)
├── duration_semesters
├── total_ects_required
└── is_active

academic_tracks
├── id (PK)
├── study_program_id (FK → study_programs)
├── name
├── code
├── description
└── is_active
```

**4. Cursus & Cours**
```
courses
├── id (PK)
├── study_program_id (FK → study_programs)
├── name
├── code (unique per program)
├── ects_credits
├── semester
├── is_mandatory
├── description
└── catalog_course_id (identifiant externe)

teaching_units
├── id (PK)
├── study_program_id (FK → study_programs)
├── name
├── code
├── ects_credits
└── is_active

semesters
├── id (PK)
├── study_program_id (FK → study_programs)
├── semester_number
├── start_date
├── end_date
└── is_active

course_prerequisites
├── id (PK)
├── course_id (FK → courses)
├── prerequisite_course_id (FK → courses)
└── is_mandatory
```

**5. Matières de l'Étudiant**
```
subjects
├── id (PK)
├── student_id (FK → users)
├── course_id (FK → courses, nullable)
├── name
├── ects_credits
├── difficulty (1-10)
├── semester
├── priority (1-10)
├── status (enum: not_started, in_progress, completed, failed)
├── exam_date
├── hours_per_week
├── description
├── catalog_course_id (synchronisation)
├── is_deleted (soft delete)
├── created_at
└── updated_at
```

**6. Inscriptions & Progression**
```
student_course_enrollments
├── id (PK)
├── student_id (FK → users)
├── course_id (FK → courses)
├── semester_id (FK → semesters)
├── enrollment_date
├── status (enum: enrolled, completed, failed, withdrawn)
└── final_grade

ects_progress
├── id (PK)
├── student_id (FK → users)
├── semester_id (FK → semesters)
├── ects_earned
├── ects_attempted
├── cumulative_ects
└── updated_at

grades
├── id (PK)
├── student_id (FK → users)
├── course_id (FK → courses)
├── grade_value
├── grade_date
├── semester_id (FK → semesters)
└── notes
```

**7. Plannings d'Études**
```
study_plans
├── id (PK)
├── student_id (FK → users)
├── name
├── week_start_date
├── week_end_date
├── status (enum: draft, active, archived)
├── generation_method (enum: ai, manual, hybrid)
├── is_validated
├── total_hours
├── created_at
└── updated_at

study_sessions
├── id (PK)
├── study_plan_id (FK → study_plans)
├── subject_id (FK → subjects)
├── day_of_week (0-6)
├── start_time
├── end_time
├── duration_minutes
├── session_type (enum: lecture, revision, exercises, project)
├── description
├── is_flexible
└── order_in_day
```

**8. Contraintes & Disponibilités**
```
availabilities
├── id (PK)
├── student_id (FK → users)
├── day_of_week (0-6)
├── start_time
├── end_time
├── is_preferred
└── created_at

constraints
├── id (PK)
├── student_id (FK → users)
├── constraint_type (enum: max_hours_per_day, min_break_duration, ...)
├── constraint_value (JSONB)
├── is_active
└── created_at
```

**9. Examens**
```
exams
├── id (PK)
├── subject_id (FK → subjects, nullable)
├── course_id (FK → courses, nullable)
├── student_id (FK → users)
├── exam_date
├── exam_time
├── duration_minutes
├── exam_type (enum: written, oral, project, practical)
├── location
├── coefficient
├── notes
└── created_at
```

**10. Notifications**
```
notifications
├── id (PK)
├── user_id (FK → users)
├── title
├── message
├── notification_type (enum: info, warning, error, success)
├── is_read
├── read_at
├── action_url
├── created_at
└── expires_at
```

**11. Logs & Audit**
```
generation_logs
├── id (PK)
├── study_plan_id (FK → study_plans)
├── generation_method (enum: ai, deterministic)
├── ai_model_used
├── input_data (JSONB)
├── output_data (JSONB)
├── validation_errors (JSONB)
├── generation_duration_ms
├── success
└── created_at

audit_logs
├── id (PK)
├── user_id (FK → users)
├── action (enum: create, update, delete, login, ...)
├── entity_type (varchar)
├── entity_id (integer)
├── old_values (JSONB)
├── new_values (JSONB)
├── ip_address
├── user_agent
└── created_at
```

**12. Administration & Rôles**
```
admin_roles
├── id (PK)
├── name (unique)
├── description
├── is_system_role
└── created_at

admin_permissions
├── id (PK)
├── role_id (FK → admin_roles)
├── resource (varchar)
├── action (enum: create, read, update, delete)
└── created_at
```

**13. Scores & Analyses**
```
priority_scores
├── id (PK)
├── subject_id (FK → subjects)
├── student_id (FK → users)
├── score (decimal)
├── factors (JSONB)
├── calculated_at
└── valid_until

risk_scores
├── id (PK)
├── student_id (FK → users)
├── subject_id (FK → subjects, nullable)
├── risk_level (enum: low, medium, high, critical)
├── risk_factors (JSONB)
├── recommendations (JSONB)
└── calculated_at

validation_rules
├── id (PK)
├── rule_name (unique)
├── rule_type (enum)
├── rule_config (JSONB)
├── is_active
└── severity (enum: error, warning, info)
```

### Relations Principales

```
users 1──────∞ student_profiles
users 1──────∞ subjects
users 1──────∞ study_plans
users 1──────∞ availabilities
users 1──────∞ constraints
users 1──────∞ exams
users 1──────∞ notifications
users 1──────∞ student_course_enrollments

study_plans 1──────∞ study_sessions

universities 1──────∞ campuses
campuses 1──────∞ study_programs
study_programs 1──────∞ courses
study_programs 1──────∞ academic_tracks
study_programs 1──────∞ semesters

courses 1──────∞ subjects
courses 1──────∞ course_prerequisites
courses 1──────∞ student_course_enrollments

subjects 1──────∞ study_sessions
subjects 1──────∞ exams
subjects 1──────∞ priority_scores
```

### Indexes pour Performance

```sql
-- Indexes sur les clés étrangères
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_subjects_student_id ON subjects(student_id);
CREATE INDEX idx_study_plans_student_id ON study_plans(student_id);
CREATE INDEX idx_study_sessions_plan_id ON study_sessions(study_plan_id);

-- Indexes composites pour requêtes fréquentes
CREATE INDEX idx_subjects_student_status ON subjects(student_id, status);
CREATE INDEX idx_study_plans_student_status ON study_plans(student_id, status);
CREATE INDEX idx_availabilities_student_day ON availabilities(student_id, day_of_week);

-- Indexes pour les recherches
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_universities_code ON universities(code);

-- Indexes pour l'audit
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## 🤖 Architecture IA

### Architecture Hybride : Déterministe + IA

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. COLLECTE DES DONNÉES                      │
│  • Profil étudiant (rythme, préférences)                       │
│  • Matières (difficulté, ECTS, examens)                        │
│  • Disponibilités horaires                                      │
│  • Contraintes personnelles                                     │
│  • Historique académique                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              2. MOTEUR DÉTERMINISTE (Planning Engine)           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  A. Calcul des Priorités                                │  │
│  │  • Proximité examen                                      │  │
│  │  • Difficulté matière                                    │  │
│  │  • ECTS / coefficient                                    │  │
│  │  • Prérequis                                             │  │
│  │  • Retard accumulé                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  B. Construction des Créneaux Valides                   │  │
│  │  • Respect des disponibilités                           │  │
│  │  • Application des contraintes                          │  │
│  │  • Équilibrage journalier                               │  │
│  │  • Pauses obligatoires                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  C. Génération du Planning de Base                      │  │
│  │  • Allocation des heures par matière                    │  │
│  │  • Distribution sur la semaine                          │  │
│  │  • Structure JSON brute                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   3. SERVICE IA (AI Service)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  A. Préparation du Contexte                             │  │
│  │  • Prompt engineering                                    │  │
│  │  • Contexte étudiant (goals, learning style)           │  │
│  │  • Planning brut en JSON                                │  │
│  │  • Contraintes et préférences                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  B. Appel au Modèle IA                                  │  │
│  │                                                           │  │
│  │  Option 1 (Production):                                 │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Google Colab + Llama 3.2 + LoRA                  │ │  │
│  │  │  • GPU T4/A100                                     │ │  │
│  │  │  • Modèle fine-tuné pour planning d'études        │ │  │
│  │  │  • Tunnel ngrok pour accès HTTP                   │ │  │
│  │  │  • Retry avec exponential backoff                 │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  Option 2 (Dev/Fallback):                               │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Ollama Local + Llama 3.2                         │ │  │
│  │  │  • Exécution locale                                │ │  │
│  │  │  • Modèle base (non fine-tuné)                    │ │  │
│  │  │  • http://127.0.0.1:11434                         │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  C. Optimisation IA                                     │  │
│  │  • Réorganisation intelligente des créneaux            │  │
│  │  • Suggestions de sessions complémentaires            │  │
│  │  • Adaptation au style d'apprentissage                │  │
│  │  • Équilibrage cognitif (matières dures/faciles)      │  │
│  │  • Recommendations personnalisées                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              4. VALIDATION SERVICE                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  A. Validation Structurelle                             │  │
│  │  • Schema JSON valide                                   │  │
│  │  • Format des dates/heures                             │  │
│  │  • Présence des champs obligatoires                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  B. Validation des Contraintes                          │  │
│  │  • Pas de chevauchements                                │  │
│  │  • Respect des disponibilités                           │  │
│  │  • Contraintes horaires (max/jour)                     │  │
│  │  • Pauses obligatoires                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  C. Auto-Correction (si possible)                       │  │
│  │  • Résolution des conflits mineurs                      │  │
│  │  • Ajustement des heures                                │  │
│  │  • Génération de warnings                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                5. SAUVEGARDE & PRÉSENTATION                     │
│  • Enregistrement en base de données                            │
│  • Création des study_sessions                                  │
│  • Log de génération (audit trail)                              │
│  • Envoi au frontend                                            │
│  • Notifications utilisateur                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Pourquoi Llama 3.2 + LoRA sur Google Colab ?

#### Avantages

1. **Coût Optimisé**
   - Google Colab Free: GPU T4 gratuit (limité)
   - Colab Pro: ~10€/mois pour GPU A100
   - **Total: 0-50€/mois** vs 200-500€/mois pour VPS GPU

2. **Performance**
   - LoRA permet le fine-tuning avec peu de données
   - Adaptation spécifique au domaine (planning d'études)
   - Latence acceptable pour génération (5-15 secondes)

3. **Scalabilité**
   - Supporte jusqu'à ~50 utilisateurs concurrents
   - Migration facile vers VPS si croissance

4. **Flexibilité**
   - Modèle base: Llama 3.2 (8B paramètres)
   - Fine-tuning rapide avec LoRA
   - Mise à jour facile du modèle

#### Architecture Technique Colab

```
Google Colab Notebook
│
├── 1. Chargement du Modèle
│   ├── unsloth (optimisation 2x plus rapide)
│   ├── Llama 3.2 base model
│   └── Adaptateurs LoRA chargés
│
├── 2. Serveur FastAPI Embarqué
│   ├── Endpoint: /v1/chat/completions
│   ├── Authentification par API key
│   └── Rate limiting
│
├── 3. Tunnel ngrok
│   ├── Expose le serveur publiquement
│   ├── URL: https://xxxx.ngrok-free.app
│   └── Renouvellement automatique
│
└── 4. Monitoring
    ├── Logs des requêtes
    ├── Performance metrics
    └── Gestion des erreurs
```

### Prompts IA

#### Exemple de Prompt pour Génération de Planning

```
Tu es un assistant spécialisé en planification d'études universitaires.

CONTEXTE ÉTUDIANT:
- Nom: {student_name}
- Programme: {study_program}
- Semestre: {current_semester}
- Rythme: {study_pace}
- Style d'apprentissage: {learning_style}
- Objectifs: {academic_goals}

MATIÈRES À PLANIFIER:
{subjects_list}

DISPONIBILITÉS HEBDOMADAIRES:
{availabilities}

CONTRAINTES:
- Maximum {max_hours_per_day}h par jour
- Pauses minimum {min_break_duration} minutes
- Pas d'étude après {max_study_time}
{custom_constraints}

PLANNING DE BASE (DÉTERMINISTE):
{base_plan}

TÂCHE:
Optimise ce planning en tenant compte du style d'apprentissage et des
objectifs de l'étudiant. Propose des ajustements intelligents pour:
1. Alterner matières difficiles et faciles
2. Placer les matières complexes aux moments de meilleure concentration
3. Ajouter des sessions de révision avant examens
4. Suggérer des sessions complémentaires si nécessaire

IMPORTANT: Retourne UNIQUEMENT un JSON valide au format exact:
{output_schema}
```

---

## 🔄 Flux de Données

### Flux d'Authentification

```
1. User → Frontend: Email + Password
2. Frontend → Backend: POST /api/v1/auth/login
3. Backend: Vérification credentials (bcrypt)
4. Backend: Génération JWT (access + refresh tokens)
5. Backend → Frontend: Tokens + User data
6. Frontend: Stockage dans localStorage
7. Frontend: Ajout token dans Axios headers
8. Requêtes suivantes: Authorization: Bearer <token>
```

### Flux de Génération de Planning

```
1. Frontend: User clique "Générer Planning"
   ↓
2. Frontend → Backend: POST /api/v1/study-plans/generate
   {
     "week_start_date": "2024-01-08",
     "generation_method": "ai"
   }
   ↓
3. Backend: Collecte des données
   • Profil étudiant
   • Matières actives
   • Disponibilités
   • Contraintes
   • Examens à venir
   ↓
4. Backend: Planning Engine (déterministe)
   • Calcul des priorités
   • Construction des créneaux
   • Génération planning de base
   ↓
5. Backend: AI Service
   • Préparation du contexte
   • Appel à Llama 3.2 (Colab ou Ollama)
   • Optimisation IA
   ↓
6. Backend: Validation Service
   • Validation schéma
   • Vérification contraintes
   • Auto-correction
   ↓
7. Backend: Sauvegarde
   • Création study_plan
   • Création study_sessions
   • Génération generation_log
   • Création notification
   ↓
8. Backend → Frontend: Planning complet
   {
     "id": 123,
     "status": "active",
     "sessions": [...],
     "warnings": [...]
   }
   ↓
9. Frontend: Affichage
   • WeeklyCalendarView
   • Statistiques
   • Warnings éventuels
   ↓
10. User: Édition manuelle possible
    • SessionEditor
    • Drag & drop (futur)
```

### Flux d'Édition de Planning

```
1. Frontend: User modifie une session
   (change horaire, durée, matière)
   ↓
2. Frontend → Backend: PUT /api/v1/study-plans/{id}/sessions/{session_id}
   {
     "start_time": "14:00",
     "end_time": "16:00",
     "subject_id": 5
   }
   ↓
3. Backend: Validation
   • Pas de chevauchement
   • Respect disponibilités
   • Respect contraintes
   ↓
4. Backend: Mise à jour
   • Update study_session
   • Recalcul total_hours du plan
   • Audit log
   ↓
5. Backend → Frontend: Session mise à jour
   ↓
6. Frontend: Mise à jour UI
   • Re-render calendrier
   • Update statistiques
```

### Flux d'Export PDF

```
1. Frontend: User clique "Exporter PDF"
   ↓
2. Frontend → Backend: GET /api/v1/study-plans/{id}/export?format=pdf
   ↓
3. Backend: Export Service
   • Récupération du planning
   • Génération PDF avec ReportLab
   • Ajout logo, graphiques, statistiques
   ↓
4. Backend → Frontend: Fichier PDF (stream)
   ↓
5. Frontend: Téléchargement automatique
```

---

## 🔒 Sécurité

### Authentification & Autorisation

#### 1. JWT (JSON Web Tokens)

```python
# Structure du token
{
  "sub": "user_email@example.com",  # Subject (user identifier)
  "user_id": 123,
  "role": "student",
  "exp": 1704672000,                    # Expiration timestamp
  "iat": 1704668400,                    # Issued at timestamp
  "type": "access"                      # Token type
}

# Access Token: 30 minutes
# Refresh Token: 7 jours
```

#### 2. Hashage des Mots de Passe

```python
# Utilisation de passlib avec Argon2
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# Hashing
hashed_password = pwd_context.hash(plain_password)

# Verification
is_valid = pwd_context.verify(plain_password, hashed_password)
```

#### 3. RBAC (Role-Based Access Control)

```python
# Rôles disponibles
ROLES = {
    "student": {
        "permissions": [
            "read:own_profile",
            "write:own_profile",
            "read:own_subjects",
            "write:own_subjects",
            "read:own_study_plans",
            "write:own_study_plans",
        ]
    },
    "admin": {
        "permissions": [
            "read:own_university_data",
            "write:own_university_data",
            "read:students",
            "write:students",
            "read:audit_logs",
        ]
    },
    "super_admin": {
        "permissions": [
            "read:all",
            "write:all",
            "delete:all",
            "manage:roles",
            "read:system_logs",
        ]
    }
}
```

#### 4. Middleware RBAC

```python
# Décorateur pour protéger les routes
@router.get("/admin/universities")
@require_role(["admin", "super_admin"])
async def get_universities(...):
    pass

# Vérification dans le middleware
def rbac_middleware(request, required_roles):
    user_role = request.user.role
    if user_role not in required_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
```

### Protection des Données

#### 1. Validation des Entrées

```python
# Pydantic schemas pour validation
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    ects_credits: int = Field(..., ge=1, le=30)
    difficulty: int = Field(..., ge=1, le=10)
    
    @validator('name')
    def validate_name(cls, v):
        # Prevent XSS
        if '<' in v or '>' in v:
            raise ValueError('Invalid characters')
        return v.strip()
```

#### 2. SQL Injection Prevention

```python
# Utilisation de SQLAlchemy ORM (parameterized queries)
# ✅ SÉCURISÉ
subjects = db.query(Subject).filter(
    Subject.student_id == student_id
).all()

# ❌ DANGEREUX (évité)
# query = f"SELECT * FROM subjects WHERE student_id = {student_id}"
```

#### 3. CORS Configuration

```python
# Configuration CORS restrictive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### 4. Rate Limiting

```python
# Protection contre les attaques par force brute
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # Max 5 tentatives par minute
async def login(...):
    pass
```

### Sécurité du Service IA

#### 1. API Key pour Colab

```python
# Configuration
COLAB_API_KEY = os.getenv("COLAB_API_KEY")

# Utilisation
headers = {
    "Authorization": f"Bearer {COLAB_API_KEY}",
    "Content-Type": "application/json"
}

response = await client.post(
    COLAB_API_URL,
    headers=headers,
    json=payload
)
```

#### 2. Validation des Réponses IA

```python
# Validation stricte du JSON retourné
try:
    ai_response = json.loads(response_text)
    # Validation avec Pydantic
    validated_plan = StudyPlanSchema(**ai_response)
except (json.JSONDecodeError, ValidationError) as e:
    # Fallback sur planning déterministe
    logger.error(f"AI response validation failed: {e}")
    return generate_fallback_plan()
```

#### 3. Sanitization des Prompts

```python
# Nettoyage des données utilisateur avant injection dans prompts
def sanitize_for_prompt(text: str) -> str:
    # Supprime les caractères potentiellement dangereux
    # Limite la longueur
    # Échappe les caractères spéciaux
    return text[:500].replace('"', '\\"').strip()
```

### Audit & Conformité

#### 1. Logging Complet

```python
# Audit de toutes les actions sensibles
audit_log = AuditLog(
    user_id=current_user.id,
    action="DELETE",
    entity_type="Subject",
    entity_id=subject_id,
    old_values=subject_dict,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
db.add(audit_log)
```

#### 2. Soft Delete

```python
# Pas de suppression définitive
class Subject(Base):
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
# Query automatique qui exclut les soft deleted
query = select(Subject).where(Subject.is_deleted == False)
```

#### 3. RGPD Compliance

```python
# Exportation des données utilisateur
@router.get("/api/v1/profile/export-data")
async def export_user_data(current_user: User = Depends(get_current_user)):
    """Export toutes les données utilisateur (RGPD)"""
    return {
        "profile": user_profile,
        "subjects": user_subjects,
        "study_plans": user_plans,
        "audit_logs": user_audit_logs
    }

# Suppression compte (anonymisation)
@router.delete("/api/v1/profile/delete-account")
async def delete_account(current_user: User = Depends(get_current_user)):
    """Anonymise les données (RGPD)"""
    current_user.email = f"deleted_{uuid4()}@deleted.com"
    current_user.full_name = "Deleted User"
    current_user.is_active = False
    # Soft delete des données liées
```

---

## 🚀 Déploiement

### Architecture de Déploiement (Production)

```
                    Internet
                       ↓
┌──────────────────────────────────────────────────────┐
│              Load Balancer (Optional)                │
│                  Nginx / Caddy                       │
└──────────────────────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│               Reverse Proxy (Nginx)                  │
│  • SSL/TLS Termination                               │
│  • Static files serving                              │
│  • Rate limiting                                     │
│  • Gzip compression                                  │
└──────────────────────────────────────────────────────┘
         ↓                              ↓
┌─────────────────┐          ┌──────────────────────┐
│  Frontend       │          │  Backend             │
│  React (SPA)    │          │  FastAPI + Uvicorn   │
│  Nginx          │          │  Gunicorn workers    │
│  Port: 80       │          │  Port: 8000          │
└─────────────────┘          └──────────────────────┘
                                      ↓
                        ┌──────────────────────┐
                        │  PostgreSQL          │
                        │  Port: 5432          │
                        │  Persistent Volume   │
                        └──────────────────────┘
                                      ↓
                        ┌──────────────────────┐
                        │  AI Service          │
                        │  Google Colab        │
                        │  + ngrok tunnel      │
                        └──────────────────────┘
```

### Docker Compose (Exemple)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: aiplanning
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/aiplanning
      SECRET_KEY: ${SECRET_KEY}
      AI_SERVICE_TYPE: ${AI_SERVICE_TYPE}
      COLAB_API_URL: ${COLAB_API_URL}
      COLAB_API_KEY: ${COLAB_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

### Variables d'Environnement

#### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aiplanning

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Service
AI_SERVICE_TYPE=colab  # ou "ollama"
COLAB_API_URL=https://xxxx.ngrok-free.app
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxx
OLLAMA_API_URL=http://127.0.0.1:11434

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=production  # ou "development"
```

#### Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=AI Study Planner
VITE_ENVIRONMENT=production
```

### Scripts de Démarrage

#### Backend (start_backend.bat)

```batch
@echo off
cd backend
call venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (start_frontend.bat)

```batch
@echo off
cd frontend
npm run dev
```

#### Tout démarrer (start_all.bat)

```batch
@echo off
echo Starting AI Study Planner...
start cmd /k "cd backend && call venv\Scripts\activate && python -m uvicorn app.main:app --reload"
timeout /t 5
start cmd /k "cd frontend && npm run dev"
echo All services started!
```

---

## 📊 Métriques & Monitoring

### Métriques Clés

1. **Performance Backend**
   - Temps de réponse API (p50, p95, p99)
   - Throughput (requêtes/seconde)
   - Taux d'erreur (%)

2. **Performance IA**
   - Latence génération planning (moyenne)
   - Taux de succès génération IA
   - Fallback rate (Ollama utilisé)

3. **Base de Données**
   - Temps de requête (moyennes)
   - Connexions actives
   - Taille de la base

4. **Utilisateurs**
   - Utilisateurs actifs (DAU, MAU)
   - Plannings générés par jour
   - Taux de satisfaction

---

## 🔗 Diagrammes Complémentaires

### Diagramme de Séquence : Génération de Planning

```
User          Frontend       Backend        Planning      AI Service     Database
 |               |              |            Engine            |              |
 |--Generate---->|              |              |               |              |
 |               |--POST /generate------------>|               |              |
 |               |              |              |               |              |
 |               |              |--Get Profile---------------------------->|
 |               |              |<-Profile Data----------------------------|
 |               |              |              |               |              |
 |               |              |--Get Subjects-------------------------->|
 |               |              |<-Subjects Data---------------------------|
 |               |              |              |               |              |
 |               |              |--Calculate-->|               |              |
 |               |              |  Priorities  |               |              |
 |               |              |<-Priority    |               |              |
 |               |              |  Scores      |               |              |
 |               |              |              |               |              |
 |               |              |--Build Base--|               |              |
 |               |              |  Plan        |               |              |
 |               |              |<-Base Plan---|               |              |
 |               |              |              |               |              |
 |               |              |--Optimize Plan-------------->|              |
 |               |              |              |               |              |
 |               |              |<-Optimized Plan--------------|              |
 |               |              |              |               |              |
 |               |              |--Validate Plan------------->|              |
 |               |              |<-Valid/Warnings-------------|              |
 |               |              |              |               |              |
 |               |              |--Save Plan-------------------------------->|
 |               |              |<-Plan ID------------------------------------|
 |               |              |              |               |              |
 |               |<-Plan JSON---|              |               |              |
 |<--Display-----|              |              |               |              |
```

---

## 📚 Documentation Complémentaire

- **[README.md](./README.md)** : Guide de démarrage rapide
- **[GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md)** : Configuration détaillée du service IA
- **[recap/PROJECT_REFERENCE.md](./recap/PROJECT_REFERENCE.md)** : Référence complète du projet
- **[recap/ARCHITECTURE_DECISIONS.md](./recap/ARCHITECTURE_DECISIONS.md)** : Décisions d'architecture
- **[backend/DATABASE_SCHEMA.md](./backend/DATABASE_SCHEMA.md)** : Schéma de base de données détaillé
- **[frontend/TESTING_GUIDE.md](./frontend/TESTING_GUIDE.md)** : Guide des tests frontend

---

## 🎯 Prochaines Évolutions

### Court Terme
- [ ] Amélioration du fine-tuning LoRA
- [ ] Interface de drag-and-drop pour les sessions
- [ ] Notifications push (PWA)
- [ ] Mode hors-ligne avec synchronisation

### Moyen Terme
- [ ] Application mobile (React Native)
- [ ] Intégration calendrier (Google Calendar, Outlook)
- [ ] Collaboration entre étudiants
- [ ] Gamification avancée

### Long Terme
- [ ] Migration vers VPS GPU (si >50 users)
- [ ] Support multi-langues complet
- [ ] Analytics avancés pour institutions
- [ ] API publique pour intégrations tierces

---

**Document créé le** : 9 Juillet 2026  
**Version** : 1.0  
**Auteur** : Équipe AI Study Planner
