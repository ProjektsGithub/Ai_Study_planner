"""
Seed script for a clean, deterministic University Defense Demo Account.
Idempotent: deletes and recreates data for the demo user so the database
is always in a known, presentation-ready state before the defense.

Demo credentials created:
    Email    : demo.soutenance@aiplaning.edu
    Password : DemoSoutenance2026!

Usage:
    cd backend
    venv\\Scripts\\python.exe seed_demo_defense.py
"""
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import app.models  # noqa: E402,F401 — ensure all SQLAlchemy mappers are registered
from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.student_profile import StudentProfile  # noqa: E402
from app.models.subject import Subject  # noqa: E402
from app.models.availability import Availability  # noqa: E402
from app.models.constraint import Constraint  # noqa: E402
from app.models.study_plan import StudyPlan  # noqa: E402
from app.models.study_session import StudySession  # noqa: E402
from app.models.exam import Exam  # noqa: E402
from app.models.grade import Grade  # noqa: E402
from app.models.ects_progress import ECTSProgress  # noqa: E402
from app.services.planning_engine import PlanningEngine  # noqa: E402
from app.services.ai_service import AIService  # noqa: E402

DEMO_EMAIL = "demo.soutenance@aiplaning.edu"
DEMO_PASSWORD = "DemoSoutenance2026!"
DEMO_NAME = "Alex Martin (Démo Soutenance)"


def current_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def seed_demo_account() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing:
            print(f"[SEED] Suppression de l'ancien compte démo (id={existing.id})...")
            db.delete(existing)
            db.commit()

        today = date.today()
        monday = current_week_monday()

        # 1. User
        user = User(
            email=DEMO_EMAIL,
            password_hash=get_password_hash(DEMO_PASSWORD),
            name=DEMO_NAME,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # 2. Student Profile
        profile = StudentProfile(
            user_id=user.id,
            cursus="Informatique & Systèmes Distribués (B.Sc.)",
            academic_level="Licence 3 / Semester 5",
            weekly_study_goal=18.0,
            semester_start_date=today - timedelta(days=45),
            semester_end_date=today + timedelta(days=60),
            exam_period_start=today + timedelta(days=21),
            total_course_hours_per_week=18.0,
            other_commitments_hours=4.0,
            preferred_study_time="morning",
            preferred_session_duration=90,
            study_pace="intensive",
            current_semester=5,
            academic_year=3,
            retake_semesters=[3],
            preferences={
                "preferred_study_times": ["morning", "afternoon"],
                "session_length": 90,
                "break_duration": 15,
            },
        )
        db.add(profile)

        # 3. Subjects (realistic mix: 1 failed retake, 1 mandatory high-coef, 3 standard)
        subjects_spec = [
            {
                "name": "Algorithmique Avancée & Graphes",
                "priority": 5,
                "difficulty": 5,
                "target_weekly_hours": 5.0,
                "exam_date": today + timedelta(days=14),
                "exam_type": "final",
                "ects_credits": 6.0,
                "coefficient": 3.0,
                "is_mandatory": True,
                "validation_status": "failed",  # Retake course -> highest priority
                "weekly_class_hours": 4.0,
                "current_progress": 35.0,
                "weak_topics": ["Plus courts chemins (Dijkstra/Bellman-Ford)", "Flots maximums", "NP-complétude"],
            },
            {
                "name": "Réseaux & Systèmes Distribués",
                "priority": 5,
                "difficulty": 4,
                "target_weekly_hours": 4.5,
                "exam_date": today + timedelta(days=18),
                "exam_type": "final",
                "ects_credits": 6.0,
                "coefficient": 2.5,
                "is_mandatory": True,
                "validation_status": "in_progress",
                "weekly_class_hours": 4.0,
                "current_progress": 50.0,
                "weak_topics": ["Consensus Raft", "Contrôle de congestion TCP", "Routage BGP"],
            },
            {
                "name": "Apprentissage Automatique (Machine Learning)",
                "priority": 4,
                "difficulty": 4,
                "target_weekly_hours": 4.0,
                "exam_date": today + timedelta(days=24),
                "exam_type": "project",
                "ects_credits": 6.0,
                "coefficient": 2.0,
                "is_mandatory": True,
                "validation_status": "in_progress",
                "weekly_class_hours": 4.0,
                "current_progress": 60.0,
                "weak_topics": ["Régularisation L1/L2", "Descente de gradient stochastique"],
            },
            {
                "name": "Bases de Données & Optimisation SQL",
                "priority": 3,
                "difficulty": 3,
                "target_weekly_hours": 2.5,
                "exam_date": today + timedelta(days=28),
                "exam_type": "midterm",
                "ects_credits": 4.0,
                "coefficient": 1.5,
                "is_mandatory": True,
                "validation_status": "in_progress",
                "weekly_class_hours": 3.0,
                "current_progress": 70.0,
                "weak_topics": ["Plans d'exécution & index B-Tree", "Isolation transactionnelle MVCC"],
            },
            {
                "name": "Génie Logiciel & Architecture Microservices",
                "priority": 3,
                "difficulty": 3,
                "target_weekly_hours": 2.0,
                "exam_date": today + timedelta(days=32),
                "exam_type": "project",
                "ects_credits": 4.0,
                "coefficient": 1.5,
                "is_mandatory": False,
                "validation_status": "in_progress",
                "weekly_class_hours": 3.0,
                "current_progress": 75.0,
                "weak_topics": ["Tests d'intégration CI/CD", "Conteneurisation Docker"],
            },
        ]

        subjects = []
        for spec in subjects_spec:
            subj = Subject(user_id=user.id, **spec)
            db.add(subj)
            subjects.append(subj)
        db.flush()

        # 4. Availabilities (5 days, balanced energy levels)
        availabilities_spec = [
            ("Monday", time(9, 0), time(12, 15), "high"),
            ("Monday", time(14, 0), time(17, 15), "medium"),
            ("Tuesday", time(9, 0), time(12, 15), "high"),
            ("Wednesday", time(14, 0), time(17, 30), "medium"),
            ("Thursday", time(9, 0), time(12, 15), "high"),
            ("Thursday", time(14, 0), time(16, 30), "low"),
            ("Saturday", time(9, 30), time(13, 0), "high"),
        ]
        for day_name, st, et, energy in availabilities_spec:
            db.add(
                Availability(
                    user_id=user.id,
                    day_of_week=day_name,
                    start_time=st,
                    end_time=et,
                    energy_level=energy,
                )
            )

        # 5. Constraints
        db.add(
            Constraint(
                user_id=user.id,
                constraint_type="max_daily_hours",
                parameters={"max_hours": 5.0},
                active=True,
            )
        )
        db.add(
            Constraint(
                user_id=user.id,
                constraint_type="required_break",
                parameters={"duration_minutes": 15, "after_minutes": 90},
                active=True,
            )
        )

        # 6. Exams & Grades & ECTS Progress for academic tracking dashboards
        for idx, subj in enumerate(subjects, start=101):
            if subj.exam_date:
                db.add(
                    Exam(
                        user_id=user.id,
                        course_id=idx,
                        course_name=subj.name,
                        exam_date=subj.exam_date,
                        exam_time=time(9, 0),
                        location="Amphithéâtre Turing — Bâtiment A",
                        exam_type=subj.exam_type or "final",
                        weight=0.6,
                        notes="Documents non autorisés",
                    )
                )

        db.add(
            Grade(
                user_id=user.id,
                course_id=101,
                course_name="Algorithmique Avancée & Graphes",
                grade_obtained=7.5,
                min_passing_grade=10.0,
                max_grade=20.0,
                validation_status="failed",
                attempt_number=1,
                semester=3,
                ects_credits=6.0,
                coefficient=3.0,
            )
        )
        db.add(
            Grade(
                user_id=user.id,
                course_id=201,
                course_name="Programmation Orientée Objet (Java/C++)",
                grade_obtained=15.5,
                min_passing_grade=10.0,
                max_grade=20.0,
                validation_status="validated",
                attempt_number=1,
                semester=4,
                ects_credits=6.0,
                coefficient=2.0,
            )
        )
        db.add(
            ECTSProgress(
                user_id=user.id,
                ects_obtained=114.0,
                ects_required=180.0,
                ects_remaining=66.0,
                progression_percentage=63.33,
            )
        )
        db.flush()

        # 7. Pre-generate a current week StudyPlan using the deterministic fallback
        # so the dashboard immediately displays a rich schedule even before clicking "Générer".
        engine = PlanningEngine(user.id, db)
        planning_data = engine.generate_planning_data(db=db)
        ai_service = AIService(db)
        fallback_data = ai_service._generate_fallback_plan(
            planning_data=planning_data,
            weekly_study_goal=profile.weekly_study_goal,
            language="fr",
        )

        study_plan = StudyPlan(
            plan_id=str(uuid.uuid4()),
            user_id=user.id,
            week_start=monday,
            status="generated",
            summary=fallback_data.get("reasoning", "Planning de démonstration pré-généré."),
            edited=False,
        )
        db.add(study_plan)
        db.flush()

        subj_by_name = {s.name: s.id for s in subjects}
        for idx, sess in enumerate(fallback_data.get("sessions", [])):
            sid = subj_by_name.get(sess["subject_name"], subjects[0].id)
            st = datetime.strptime(sess["start_time"], "%H:%M:%S").time()
            et = datetime.strptime(sess["end_time"], "%H:%M:%S").time()
            completed = idx < 3  # Mark first 3 sessions as completed for realistic progress charts
            db.add(
                StudySession(
                    study_plan_id=study_plan.id,
                    subject_id=sid,
                    day=sess["day"],
                    start_time=st,
                    end_time=et,
                    task_type=sess["task_type"],
                    notes=sess["notes"],
                    completed=completed,
                    completed_at=datetime.now(timezone.utc) if completed else None,
                )
            )

        db.commit()
        print("=" * 68)
        print("✅ COMPTE DE DÉMONSTRATION SOUTENANCE PRÊT")
        print("=" * 68)
        print(f"  Utilisateur ID : {user.id}")
        print(f"  Email          : {DEMO_EMAIL}")
        print(f"  Mot de passe   : {DEMO_PASSWORD}")
        print(f"  Semaine active : {monday.isoformat()}")
        print(f"  Matières       : {len(subjects)} (dont 1 matière en rattrapage prioritaire)")
        print(f"  Séances créées : {len(fallback_data.get('sessions', []))} (dont 3 complétées)")
        print("=" * 68)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_account()
