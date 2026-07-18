"""
Setup automatique complet AI Study Planner
Une seule commande pour tout installer
"""
import os
import sys
import subprocess
from pathlib import Path

def print_step(step, message):
    print(f"\n{'='*60}")
    print(f"  [{step}] {message}")
    print('='*60)

def run_command(cmd, cwd=None, check=True):
    """Exécute une commande et affiche le résultat"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Erreur: {e.stderr}")
        return False

def detect_postgres_user():
    """Détecte l'utilisateur PostgreSQL valide"""
    import psycopg
    
    users = [os.environ.get('USERNAME'), 'postgres', 'user']
    
    for user in users:
        if not user:
            continue
        try:
            conn = psycopg.connect(
                host="localhost",
                port=5432,
                dbname="postgres",
                user=user,
                autocommit=True
            )
            conn.close()
            return user
        except:
            continue
    
    return None

def create_database(pg_user):
    """Crée la base de données"""
    import psycopg
    
    try:
        conn = psycopg.connect(
            host="localhost",
            port=5432,
            dbname="postgres",
            user=pg_user,
            autocommit=True
        )
        cur = conn.cursor()
        
        # Vérifier si existe
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_study_planner'")
        if cur.fetchone():
            print("✓ Base de données existe déjà")
        else:
            cur.execute("CREATE DATABASE ai_study_planner")
            print("✓ Base de données créée")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erreur création BD: {e}")
        return False

def create_env_file(pg_user):
    """Crée le fichier .env avec la bonne config"""
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    
    # Lire .env.example
    if env_example.exists():
        content = env_example.read_text(encoding='utf-8')
    else:
        content = ""
    
    # Remplacer DATABASE_URL
    lines = []
    found_db_url = False
    for line in content.split('\n'):
        if line.startswith('DATABASE_URL='):
            lines.append(f'DATABASE_URL=postgresql+psycopg://{pg_user}@localhost:5432/ai_study_planner')
            found_db_url = True
        else:
            lines.append(line)
    
    # Si pas trouvé, ajouter
    if not found_db_url:
        lines.insert(0, f'DATABASE_URL=postgresql+psycopg://{pg_user}@localhost:5432/ai_study_planner')
    
    env_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✓ Fichier .env créé avec utilisateur: {pg_user}")
    return True

def main():
    print("\n" + "="*60)
    print("  SETUP AUTOMATIQUE - AI STUDY PLANNER")
    print("="*60)
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Étape 1: Vérifier Python
    print_step("1/7", "Vérification Python")
    if not run_command("py --version"):
        print("✗ Python non trouvé. Installez Python 3.11+")
        sys.exit(1)
    print("✓ Python OK")
    
    # Étape 2: Créer venv
    print_step("2/7", "Environnement virtuel")
    venv_path = Path("venv")
    if not venv_path.exists():
        if not run_command("py -m venv venv"):
            print("✗ Échec création venv")
            sys.exit(1)
        print("✓ Environnement virtuel créé")
    else:
        print("✓ Environnement virtuel existe")
    
    # Étape 3: Installer psycopg (pour détecter user)
    print_step("3/7", "Installation psycopg")
    activate = "venv\\Scripts\\activate.bat &&" if os.name == 'nt' else "source venv/bin/activate &&"
    run_command(f"{activate} pip install psycopg[binary] -q")
    
    # Activer venv pour les imports Python
    sys.path.insert(0, str(venv_path / "Lib" / "site-packages"))
    
    # Étape 4: Détecter user PostgreSQL
    print_step("4/7", "Détection utilisateur PostgreSQL")
    pg_user = detect_postgres_user()
    if not pg_user:
        print("✗ Impossible de se connecter à PostgreSQL")
        print("Vérifiez que PostgreSQL est démarré dans Laragon")
        sys.exit(1)
    print(f"✓ Utilisateur PostgreSQL: {pg_user}")
    
    # Étape 5: Créer BD
    print_step("5/7", "Création base de données")
    if not create_database(pg_user):
        sys.exit(1)
    
    # Étape 6: Créer .env
    print_step("6/7", "Configuration .env")
    if not create_env_file(pg_user):
        sys.exit(1)
    
    # Étape 7: Installer dépendances
    print_step("7/7", "Installation dépendances")
    if not run_command(f"{activate} pip install -r requirements.txt -q"):
        print("✗ Échec installation dépendances")
        sys.exit(1)
    print("✓ Dépendances installées")
    
    # Étape 8: Migrations
    print_step("8/9", "Migrations base de données")
    if not run_command(f"{activate} alembic upgrade head"):
        print("✗ Échec migrations")
        sys.exit(1)
    print("✓ Migrations appliquées")
    
    # Étape 9: Créer admin
    print_step("9/9", "Création compte Super Admin")
    if not run_command(f"{activate} python scripts\\seed_admin.py"):
        print("⚠ Admin peut-être déjà créé")
    
    # Succès
    print("\n" + "="*60)
    print("  ✓ INSTALLATION TERMINÉE !")
    print("="*60)
    print()
    print("Identifiants Super Admin:")
    print("  Email:    admin@example.com")
    print("  Password: Admin123!")
    print()
    print("Pour démarrer le serveur:")
    print("  cd backend")
    print("  .\\start_backend.bat")
    print()
    print("Backend: http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Installation annulée")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        sys.exit(1)
