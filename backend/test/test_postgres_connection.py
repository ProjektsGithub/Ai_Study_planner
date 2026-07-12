"""
Script pour tester différentes configurations de connexion PostgreSQL
"""
import sys

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
except ImportError:
    print("✗ SQLAlchemy n'est pas installé")
    print("Installation: py -m pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# Différentes configurations à tester
configs = [
    {
        "name": "Laragon par défaut (postgres/root)",
        "url": "postgresql://postgres:root@localhost:5432/postgres"
    },
    {
        "name": "Laragon (postgres/postgres)",
        "url": "postgresql://postgres:postgres@localhost:5432/postgres"
    },
    {
        "name": "Laragon (postgres sans mot de passe)",
        "url": "postgresql://postgres@localhost:5432/postgres"
    },
    {
        "name": "Laragon (root/root)",
        "url": "postgresql://root:root@localhost:5432/postgres"
    },
    {
        "name": "Laragon (root sans mot de passe)",
        "url": "postgresql://root@localhost:5432/postgres"
    },
]

print("=" * 60)
print("Test de connexion PostgreSQL")
print("=" * 60)
print()

successful_config = None

for config in configs:
    print(f"Test: {config['name']}")
    print(f"URL: {config['url'].replace(':', ':***').split('@')[0]}@{config['url'].split('@')[1]}")
    
    try:
        engine = create_engine(config['url'], connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ CONNEXION RÉUSSIE!")
            print(f"  Version: {version.split(',')[0]}")
            
            # Vérifier si la base de données existe
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'ai_study_planner'")
            )
            db_exists = result.fetchone()
            
            if db_exists:
                print(f"  ✓ Base de données 'ai_study_planner' existe déjà")
            else:
                print(f"  ℹ Base de données 'ai_study_planner' n'existe pas encore")
            
            successful_config = config
            print()
            break
            
    except OperationalError as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            print("✗ Échec: Mot de passe incorrect")
        elif "Connection refused" in error_msg or "could not connect" in error_msg:
            print("✗ Échec: PostgreSQL ne répond pas (est-il démarré dans Laragon?)")
        elif "timeout" in error_msg:
            print("✗ Échec: Timeout de connexion")
        else:
            print(f"✗ Échec: {error_msg[:100]}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    print()

print("=" * 60)

if successful_config:
    print("✓ Configuration trouvée!")
    print()
    print("Mettez à jour votre fichier .env avec:")
    print()
    print(f"DATABASE_URL={successful_config['url'].replace('/postgres', '/ai_study_planner')}")
    print()
    print("Ensuite, exécutez:")
    print("  py create_db_sqlalchemy.py")
else:
    print("✗ Aucune configuration ne fonctionne")
    print()
    print("Vérifications à faire:")
    print("1. PostgreSQL est-il démarré dans Laragon?")
    print("   → Ouvrez Laragon et cliquez sur 'Start All'")
    print()
    print("2. Vérifiez le port utilisé:")
    print("   → Dans Laragon: Menu → PostgreSQL → Port")
    print()
    print("3. Essayez de vous connecter avec HeidiSQL:")
    print("   → Laragon → Database → PostgreSQL")

print("=" * 60)
