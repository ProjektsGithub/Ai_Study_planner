"""
Seed demo university timetables (emplois du temps fictifs) for all programs.
"""
from app.core.database import SessionLocal
from app.models.study_program import StudyProgram
from app.models.class_schedule import ClassSchedule
from app.models.student_profile import StudentProfile
from datetime import time

DEMO_CLASSES = [
    # Computer Science / Licence Informatique
    {"course_name": "Algorithmique & Structures de Donnees", "course_code": "INF101", "day": "Monday", "start": time(8, 30), "end": time(10, 30), "type": "CM", "room": "Amphi Alan Turing"},
    {"course_name": "Algorithmique (Travaux Diriges)", "course_code": "INF101-TD", "day": "Monday", "start": time(11, 0), "end": time(13, 0), "type": "TD", "room": "Salle TD 204"},
    {"course_name": "Architecture des Ordinateurs", "course_code": "INF102", "day": "Tuesday", "start": time(9, 0), "end": time(12, 0), "type": "CM", "room": "Amphi Neumann"},
    {"course_name": "Bases de Donnees Relationnelles", "course_code": "INF103", "day": "Wednesday", "start": time(8, 30), "end": time(11, 30), "type": "CM", "room": "Amphi Turing"},
    {"course_name": "Bases de Donnees (TP SQL)", "course_code": "INF103-TP", "day": "Wednesday", "start": time(14, 0), "end": time(17, 0), "type": "TP", "room": "Labo Info 3"},
    {"course_name": "Developpement Web Fullstack", "course_code": "INF104", "day": "Thursday", "start": time(10, 0), "end": time(12, 30), "type": "CM", "room": "Amphi Lovelace"},
    {"course_name": "Projet Web & Reseau", "course_code": "INF104-TP", "day": "Friday", "start": time(14, 0), "end": time(17, 0), "type": "TP", "room": "Labo Info 1"},

    # General Sciences / Ingénierie
    {"course_name": "Mathematiques pour l'Ingenieur", "course_code": "MAT101", "day": "Monday", "start": time(14, 0), "end": time(16, 0), "type": "CM", "room": "Amphi Principal"},
    {"course_name": "Physique Fondamentale & Mecanique", "course_code": "PHY101", "day": "Tuesday", "start": time(14, 0), "end": time(16, 30), "type": "CM", "room": "Amphi Newton"},
    {"course_name": "Anglais Technique & Communication", "course_code": "ANG101", "day": "Wednesday", "start": time(11, 45), "end": time(13, 15), "type": "TD", "room": "Salle 305"},
    {"course_name": "Systemes & Reseaux", "course_code": "SYS101", "day": "Thursday", "start": time(8, 30), "end": time(10, 0), "type": "CM", "room": "Amphi Curie"},
]

def seed():
    db = SessionLocal()
    try:
        programs = db.query(StudyProgram).filter(StudyProgram.is_deleted == False).all()
        if not programs:
            p = StudyProgram(name="Informatique & Intelligence Artificielle", code="INFO-IA", description="Licence Info")
            db.add(p)
            db.commit()
            db.refresh(p)
            programs = [p]

        print(f"Trouve {len(programs)} filieres d'etudes.")

        # Clear previous demo schedules
        db.query(ClassSchedule).delete()
        db.commit()

        inserted_count = 0
        for p in programs:
            for item in DEMO_CLASSES:
                cs = ClassSchedule(
                    study_program_id=p.id,
                    course_name=item["course_name"],
                    course_code=item["course_code"],
                    day_of_week=item["day"],
                    start_time=item["start"],
                    end_time=item["end"],
                    session_type=item["type"],
                    room_location=item["room"],
                    is_mandatory=True
                )
                db.add(cs)
                inserted_count += 1

        db.commit()
        print(f"[OK] Seeding termine : {inserted_count} creneaux d'emplois du temps crees pour {len(programs)} filieres.")

        # Ensure all student profiles are assigned a filiere_id so they detect this timetable!
        first_program = programs[0]
        profiles = db.query(StudentProfile).all()
        updated_profiles = 0
        for prof in profiles:
            if not prof.filiere_id:
                prof.filiere_id = first_program.id
                prof.current_semester = 1
                updated_profiles += 1
        db.commit()
        print(f"[OK] {updated_profiles} profil(s) etudiant(s) meches sur la filiere ID {first_program.id} ({first_program.name}).")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
