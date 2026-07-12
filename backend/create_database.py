"""
Script pour créer la base de données ai_study_planner
"""
import sys
import psycopg

try:
    # Connexion à la base postgres par défaut
    conn = psycopg.connect("host=localhost port=5432 dbname=postgres user=user", autocommit=True)
    cur = conn.cursor()
    
    # Vérifier si la base existe
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_study_planner'")
    exists = cur.fetchone()
    
    if exists:
        print("✓ La base de données 'ai_study_planner' existe déjà")
    else:
        # Créer la base de données
        cur.execute("CREATE DATABASE ai_study_planner")
        print("✓ Base de données 'ai_study_planner' créée avec succès")
    
    cur.close()
    conn.close()
    
    print("\nProchaine étape:")
    print("  py -m alembic upgrade head")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    sys.exit(1)
