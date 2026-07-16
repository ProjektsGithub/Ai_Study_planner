"""
Script pour créer la base de données ai_study_planner
Compatible avec Laragon (utilise le nom d'utilisateur Windows)
"""
import sys
import os
import psycopg

def get_db_user():
    """Détecte l'utilisateur PostgreSQL (Windows username pour Laragon)"""
    return os.environ.get('USERNAME', 'postgres')

def create_database():
    """Crée la base de données ai_study_planner"""
    db_user = get_db_user()
    db_name = 'ai_study_planner'
    
    print("=" * 50)
    print("  Création Base de Données PostgreSQL")
    print("=" * 50)
    print()
    print(f"Utilisateur PostgreSQL: {db_user}")
    print(f"Base de données: {db_name}")
    print()
    
    # Liste des utilisateurs à essayer
    users_to_try = [db_user, 'postgres', 'user']
    
    for user in users_to_try:
        try:
            print(f"Tentative de connexion avec l'utilisateur '{user}'...")
            
            # Connexion à la base postgres par défaut
            conn = psycopg.connect(
                host="localhost",
                port=5432,
                dbname="postgres",
                user=user,
                autocommit=True
            )
            cur = conn.cursor()
            
            # Vérifier si la base existe
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = cur.fetchone()
            
            if exists:
                print(f"✓ La base de données '{db_name}' existe déjà")
            else:
                # Créer la base de données
                cur.execute(f"CREATE DATABASE {db_name}")
                print(f"✓ Base de données '{db_name}' créée avec succès")
            
            cur.close()
            conn.close()
            
            print()
            print("=" * 50)
            print("  Configuration")
            print("=" * 50)
            print()
            print("Utilisateur PostgreSQL utilisé:", user)
            print(f"DATABASE_URL: postgresql+psycopg://{user}@localhost:5432/{db_name}")
            print()
            print("Prochaines étapes:")
            print("  1. Vérifier le .env (DATABASE_URL)")
            print("  2. py -m alembic upgrade head")
            print("  3. python scripts\\seed_admin.py")
            print()
            
            return True
            
        except psycopg.OperationalError as e:
            print(f"✗ Échec avec '{user}': {e}")
            continue
        except Exception as e:
            print(f"✗ Erreur inattendue avec '{user}': {e}")
            continue
    
    print()
    print("=" * 50)
    print("  Erreur: Impossible de se connecter à PostgreSQL")
    print("=" * 50)
    print()
    print("Solutions possibles:")
    print("  1. Vérifier que PostgreSQL est démarré dans Laragon")
    print("  2. Vérifier que le port 5432 est correct")
    print("  3. Essayer manuellement:")
    print(f"     psql -U {db_user} -c \"CREATE DATABASE {db_name};\"")
    print()
    return False

if __name__ == "__main__":
    try:
        success = create_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur fatale: {e}")
        sys.exit(1)
