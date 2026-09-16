"""
Script pour créer des semestres manquants pour tous les cursus (academic tracks)
"""
from app.core.database import SessionLocal
from app.models.semester import Semester
from app.models.academic_track import AcademicTrack
from datetime import datetime

db = SessionLocal()

try:
    print("🔍 Vérification des cursus sans semestres...")
    
    # Get all academic tracks
    tracks = db.query(AcademicTrack).filter(AcademicTrack.is_deleted == False).all()
    
    tracks_without_semesters = []
    
    for track in tracks:
        # Check if track has semesters
        semester_count = db.query(Semester).filter(
            Semester.academic_track_id == track.id,
            Semester.is_deleted == False
        ).count()
        
        if semester_count == 0:
            tracks_without_semesters.append(track)
    
    print(f"\n📊 Trouvé {len(tracks_without_semesters)} cursus sans semestres sur {len(tracks)} cursus totaux")
    
    if not tracks_without_semesters:
        print("✅ Tous les cursus ont déjà des semestres!")
        exit(0)
    
    print("\n🔧 Création des semestres pour chaque cursus...")
    
    created_count = 0
    
    for track in tracks_without_semesters:
        print(f"\n  📝 Cursus: {track.name} (ID: {track.id})")
        
        # Créer 6 semestres pour chaque cursus (S1 à S6)
        for sem_num in range(1, 7):
            semester = Semester(
                academic_track_id=track.id,
                name=f"Semestre {sem_num}",
                name_de=f"Semester {sem_num}",
                semester_number=sem_num,
                description=f"Semester {sem_num} of {track.name}",
                description_de=f"Semester {sem_num} von {track.name}",
                ects_required=30.0,  # Standard ECTS per semester
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(semester)
            created_count += 1
            print(f"    ✅ Créé S{sem_num}")
    
    db.commit()
    print(f"\n✅ Succès! {created_count} semestres créés pour {len(tracks_without_semesters)} cursus")
    print("\n🎉 Base de données mise à jour!")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    db.rollback()
finally:
    db.close()
