"""
Script pour supprimer TOUS les cours (actifs + supprimés) pour repartir à zéro
"""
from app.core.database import SessionLocal
from app.models.course import Course

def reset_all_courses():
    print("=" * 80)
    print("SUPPRESSION TOTALE DE TOUS LES COURS")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Compter tous les cours
        all_courses = db.query(Course).all()
        count = len(all_courses)
        
        active_count = sum(1 for c in all_courses if not c.is_deleted)
        deleted_count = sum(1 for c in all_courses if c.is_deleted)
        
        print(f"\n📊 Trouvé {count} cours au total:")
        print(f"   - {active_count} cours ACTIFS")
        print(f"   - {deleted_count} cours SUPPRIMÉS (soft delete)")
        
        if count == 0:
            print("\n✅ La base est déjà vide!")
            return
        
        # Demander confirmation
        print("\n⚠️  ATTENTION EXTRÊME:")
        print("   Cette opération va SUPPRIMER DÉFINITIVEMENT TOUS LES COURS.")
        print("   Cela inclut les cours actifs utilisés par les étudiants!")
        print("   Cette action est IRRÉVERSIBLE.")
        
        response = input("\n   Taper 'SUPPRIMER TOUT' pour confirmer: ").strip()
        
        if response != "SUPPRIMER TOUT":
            print("\n❌ Opération annulée par sécurité.")
            return
        
        # Supprimer tous les cours
        print(f"\n🗑️  Suppression de {count} cours...")
        
        for course in all_courses:
            db.delete(course)
        
        db.commit()
        
        print(f"\n✅ {count} cours supprimés définitivement!")
        print("   La base de données est maintenant vide.")
        print("   Vous pouvez faire un import complet depuis Excel.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur: {e}")
    finally:
        db.close()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    reset_all_courses()
