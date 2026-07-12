"""
Test complet de génération avec tous les logs pour débugger
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.study_plan_service import StudyPlanService

async def test_full_generation():
    db: Session = SessionLocal()
    
    print("=" * 70)
    print("TEST COMPLET DE GENERATION DE PLAN")
    print("=" * 70)
    
    # Trouver le dernier utilisateur
    user = db.query(User).order_by(User.id.desc()).first()
    
    if not user:
        print("\nAucun utilisateur trouve")
        return
    
    print(f"\nUtilisateur : {user.name} (ID: {user.id})")
    
    # Calculer le lundi de cette semaine
    today = date.today()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    
    print(f"Generation pour la semaine du : {monday}")
    print(f"\nLancement de la generation (cela peut prendre 10-30 secondes)...\n")
    
    # Créer le service
    service = StudyPlanService(db)
    
    # Générer
    try:
        success, result = service.generate_plan(
            user_id=user.id,
            week_start=monday,
            force_regenerate=True
        )
        
        print("\n" + "=" * 70)
        if success:
            print("GENERATION REUSSIE !")
            print("=" * 70)
            print(f"\nResume :")
            print(f"   Plan ID : {result.get('plan_id')}")
            print(f"   Total heures : {result.get('total_hours', 0)}h")
            print(f"   Sessions : {result.get('session_count', 0)}")
            
            if result.get('sessions'):
                print(f"\nSessions generees :")
                for sess in result['sessions'][:10]:  # Afficher les 10 premières
                    print(f"   - {sess['day']} {sess['start_time']}-{sess['end_time']} : {sess.get('subject_name', 'Unknown')}")
                
                if len(result['sessions']) > 10:
                    print(f"   ... et {len(result['sessions']) - 10} autres sessions")
            else:
                print(f"\nAucune session dans le resultat")
                
            if result.get('warnings'):
                print(f"\nAvertissements ({len(result['warnings'])}) :")
                for warn in result['warnings'][:5]:
                    print(f"   - {warn}")
                    
        else:
            print("GENERATION ECHOUEE !")
            print("=" * 70)
            error_type = result.get('error', 'unknown')
            message = result.get('message', 'No message')
            
            print(f"\nErreur : {error_type}")
            print(f"   Message : {message}")
            
            if result.get('validation_errors'):
                print(f"\nErreurs de validation :")
                for err in result['validation_errors']:
                    print(f"   - {err}")
                    
            if result.get('warnings'):
                print(f"\nAvertissements :")
                for warn in result['warnings']:
                    print(f"   - {warn}")
                    
            if result.get('details'):
                print(f"\nDetails :")
                details = result['details']
                if isinstance(details, dict):
                    if 'error' in details:
                        print(f"   Erreur AI : {details['error']}")
                    if 'plan' in details:
                        plan = details['plan']
                        if isinstance(plan, dict):
                            print(f"   Sessions dans plan AI : {len(plan.get('sessions', []))}")
                        
    except Exception as e:
        print(f"\nEXCEPTION : {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_full_generation())
