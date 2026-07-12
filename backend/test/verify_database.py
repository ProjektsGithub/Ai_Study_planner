"""
Script pour vérifier que toutes les tables ont été créées
"""
import psycopg

try:
    conn = psycopg.connect("host=localhost port=5432 dbname=ai_study_planner user=user")
    cur = conn.cursor()
    
    # Lister toutes les tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    
    print("=" * 70)
    print("Tables créées dans la base de données 'ai_study_planner':")
    print("=" * 70)
    print()
    
    if tables:
        for i, (table,) in enumerate(tables, 1):
            print(f"  {i}. {table}")
        print()
        print(f"✓ Total: {len(tables)} tables créées")
    else:
        print("✗ Aucune table trouvée")
    
    print()
    print("=" * 70)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Erreur: {e}")
