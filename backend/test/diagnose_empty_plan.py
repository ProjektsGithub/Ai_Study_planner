"""
Script de diagnostic pour comprendre pourquoi un plan vide est généré
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession

def diagnose():
    db: Session = SessionLocal()
    
    print("=" * 70)
    print("🔍 DIAGNOSTIC DU PROFIL UTILISATEUR")
    print("=" * 70)
    
    # Trouver le dernier utilisateur créé
    user = db.query(User).order_by(User.id.desc()).first()
    
    if not user:
        print("\n❌ Aucun utilisateur trouvé dans la base de données")
        return
    
    print(f"\n👤 Utilisateur : {user.name} (ID: {user.id})")
    print(f"   Email : {user.email}")
    
    # Vérifier les matières
    subjects = db.query(Subject).filter(Subject.user_id == user.id).all()
    print(f"\n📚 Matières configurées : {len(subjects)}")
    
    if subjects:
        for subj in subjects:
            print(f"   - {subj.name} (Priority: {subj.priority})")
    else:
        print("   ⚠️  AUCUNE MATIÈRE configurée !")
        print("   → Allez dans l'interface pour ajouter des matières")
    
    # Vérifier les disponibilités
    availabilities = db.query(Availability).filter(Availability.user_id == user.id).all()
    print(f"\n⏰ Disponibilités configurées : {len(availabilities)}")
    
    if availabilities:
        by_day = {}
        for av in availabilities:
            if av.day_of_week not in by_day:
                by_day[av.day_of_week] = []
            by_day[av.day_of_week].append(av)
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            if day in by_day:
                print(f"   {day}:")
                for av in by_day[day]:
                    print(f"     {av.start_time} - {av.end_time} (Energy: {av.energy_level})")
    else:
        print("   ⚠️  AUCUNE DISPONIBILITÉ configurée !")
        print("   → Allez dans l'interface pour ajouter des créneaux horaires")
    
    # Vérifier le dernier plan généré
    last_plan = db.query(StudyPlan).filter(
        StudyPlan.user_id == user.id
    ).order_by(StudyPlan.created_at.desc()).first()
    
    if last_plan:
        print(f"\n📅 Dernier plan généré :")
        print(f"   ID: {last_plan.id}")
        print(f"   Semaine: {last_plan.week_start}")
        print(f"   Summary (brut): {repr(last_plan.summary)}")
        
        import json
        try:
            summary_data = json.loads(last_plan.summary) if last_plan.summary else {}
            print(f"   Total heures: {summary_data.get('total_hours', 0)}h")
        except:
            print(f"   ⚠️  Summary invalide ou vide")
            summary_data = {}
        
        print(f"   Status: {last_plan.status}")
        
        sessions = db.query(StudySession).filter(
            StudySession.study_plan_id == last_plan.id
        ).all()
        
        print(f"   Sessions: {len(sessions)}")
        
        if sessions:
            for sess in sessions[:5]:  # Afficher les 5 premières
                subject = db.query(Subject).filter(Subject.id == sess.subject_id).first()
                print(f"     - {sess.day} {sess.start_time}-{sess.end_time} : {subject.name if subject else 'Unknown'}")
        else:
            print("     ⚠️  AUCUNE SESSION générée !")
            print("     → Le plan est vide malgré la génération")
    else:
        print("\n📅 Aucun plan n'a encore été généré")
    
    print("\n" + "=" * 70)
    print("💡 RECOMMANDATIONS")
    print("=" * 70)
    
    if len(subjects) == 0:
        print("\n1️⃣  AJOUTER DES MATIÈRES")
        print("   → Allez dans 'Profil' ou 'Matières'")
        print("   → Ajoutez au moins 1 matière avec une priorité")
    
    if len(availabilities) == 0:
        print("\n2️⃣  AJOUTER DES DISPONIBILITÉS")
        print("   → Allez dans 'Disponibilités'")
        print("   → Ajoutez des créneaux horaires pour chaque jour de la semaine")
    
    if len(subjects) > 0 and len(availabilities) > 0:
        print("\n✅ Configuration OK")
        print("   → Le problème vient probablement de l'IA ou du parsing JSON")
        print("   → Vérifiez les logs du backend pendant la génération")
    
    print("\n")
    
    db.close()

if __name__ == "__main__":
    diagnose()
