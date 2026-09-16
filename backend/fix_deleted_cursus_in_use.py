"""
Script pour restaurer les cursus supprimés mais encore utilisés par des étudiants
et créer leurs semestres manquants
"""
from app.core.database import SessionLocal
from app.models.semester import Semester
from app.models.academic_track import AcademicTrack
from app.models.student_profile import StudentProfile
from datetime import datetime

db = SessionLocal()

try:
    print("🔍 Recherche des cursus supprimés encore utilisés...")
    
    # Get all student profiles with cursus_id
    profiles = db.query(StudentProfile).filter(StudentProfile.cursus_id.isnot(None)).all()
    
    cursus_ids_in_use = list(set([p.cursus_id for p in profiles]))
    print(f"  Cursus utilisés par les étudiants: {len(cursus_ids_in_use)}")
    
    # Find deleted cursus still in use
    deleted_cursus_in_use = db.query(AcademicTrack).filter(
        AcademicTrack.id.in_(cursus_ids_in_use),
        AcademicTrack.is_deleted == True
    ).all()
    
    print(f"\n❌ Trouvé {len(deleted_cursus_in_use)} cursus supprimés encore utilisés:")
    for track in deleted_cursus_in_use:
        users_count = db.query(StudentProfile).filter(StudentProfile.cursus_id == track.id).count()
        print(f"  - ID {track.id}: {track.name} ({users_count} étudiants)")
    
    if not deleted_cursus_in_use:
        print("✅ Aucun cursus supprimé en cours d'utilisation!")
        exit(0)
    
    print("\n🔧 Restauration des cursus...")
    
    for track in deleted_cursus_in_use:
        track.is_deleted = False
        track.deleted_at = None
        track.updated_at = datetime.utcnow()
        print(f"  ✅ Restauré: {track.name} (ID: {track.id})")
    
    db.commit()
    print("\n✅ Cursus restaurés!")
    
    print("\n🔧 Création des semestres manquants...")
    
    created_count = 0
    for track in deleted_cursus_in_use:
        # Check if track has semesters
        semester_count = db.query(Semester).filter(
            Semester.academic_track_id == track.id,
            Semester.is_deleted == False
        ).count()
        
        if semester_count == 0:
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
                    ects_required=30.0,
                    is_deleted=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(semester)
                created_count += 1
                print(f"    ✅ Créé S{sem_num}")
        else:
            print(f"  ✅ {track.name} a déjà {semester_count} semestres")
    
    db.commit()
    print(f"\n✅ Succès! {created_count} semestres créés")
    print("\n🎉 Base de données corrigée!")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
