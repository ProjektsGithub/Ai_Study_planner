"""
Script pour supprimer DÉFINITIVEMENT (hard delete) les cours marqués comme supprimés
Cela permettra de résoudre les conflits de contrainte unique lors des imports
"""
from app.core.database import SessionLocal
from app.models.course import Course

def clean_deleted_courses():
    print("=" * 80)
    print("NETTOYAGE DES COURS SUPPRIMÉS (HARD DELETE)")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Compter les cours supprimés
        deleted_courses = db.query(Course).filter(Course.is_deleted == True).all()
        count = len(deleted_courses)
        
        print(f"\n📊 Trouvé {count} cours marqués comme supprimés (soft delete)")
        
        if count == 0:
            print("✅ Aucun nettoyage nécessaire!")
            return
        
        # Demander confirmation
        print("\n⚠️  ATTENTION: Cette opération va SUPPRIMER DÉFINITIVEMENT ces cours de la base de données.")
        print("   Cela résoudra les conflits de contrainte unique lors des imports.")
        print("\n   Les cours ACTIFS ne seront PAS affectés.")
        
        response = input("\n   Continuer? (oui/non): ").strip().lower()
        
        if response not in ['oui', 'yes', 'y', 'o']:
            print("\n❌ Opération annulée.")
            return
        
        # Supprimer les cours
        print(f"\n🗑️  Suppression de {count} cours...")
        
        for course in deleted_courses:
            db.delete(course)
        
        db.commit()
        
        print(f"\n✅ {count} cours supprimés définitivement!")
        print("   La contrainte unique sur les codes de cours est maintenant propre.")
        print("   Vous pouvez réessayer l'import Excel.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur: {e}")
    finally:
        db.close()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    clean_deleted_courses()
