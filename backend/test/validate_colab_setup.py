"""
Script de validation de la configuration Google Colab

Vérifie que tous les fichiers et configurations nécessaires sont en place.

Usage:
    python validate_colab_setup.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Afficher un en-tête"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Afficher un message de succès"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Afficher un message d'erreur"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Afficher un avertissement"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Afficher une info"""
    print(f"   {text}")


def check_files():
    """Vérifier que tous les fichiers nécessaires existent"""
    print_header("Vérification des fichiers")
    
    required_files = [
        ("notebooks/colab_inference_server.ipynb", "Notebook Colab"),
        ("notebooks/README.md", "Documentation notebooks"),
        ("backend/test_colab_connection.py", "Script de test"),
        ("backend/.env.example", "Template .env"),
        ("GOOGLE_COLAB_SETUP.md", "Documentation complète"),
        ("QUICK_START_COLAB.md", "Guide rapide"),
    ]
    
    all_exist = True
    
    for file_path, description in required_files:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            print_success(f"{description}: {file_path}")
        else:
            print_error(f"{description} manquant: {file_path}")
            all_exist = False
    
    return all_exist


def check_env_config():
    """Vérifier la configuration .env"""
    print_header("Vérification de la configuration")
    
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print_error(".env n'existe pas")
        print_info("Copiez .env.example vers .env")
        return False
    
    print_success(".env existe")
    
    # Charger les variables
    load_dotenv(env_path)
    
    # Vérifier les variables importantes
    checks = []
    
    ai_service_type = os.getenv('AI_SERVICE_TYPE')
    if ai_service_type:
        if ai_service_type == 'colab':
            print_success(f"AI_SERVICE_TYPE = {ai_service_type} (mode Colab)")
            checks.append(True)
        elif ai_service_type == 'ollama':
            print_warning(f"AI_SERVICE_TYPE = {ai_service_type} (mode local)")
            print_info("Pour utiliser Colab, changez en 'colab'")
            checks.append(True)
        else:
            print_error(f"AI_SERVICE_TYPE invalide: {ai_service_type}")
            checks.append(False)
    else:
        print_warning("AI_SERVICE_TYPE non défini (par défaut: ollama)")
        checks.append(True)
    
    # Si mode Colab, vérifier COLAB_API_URL et COLAB_API_KEY
    if ai_service_type == 'colab':
        colab_url = os.getenv('COLAB_API_URL')
        if colab_url:
            if 'ngrok' in colab_url:
                print_success(f"COLAB_API_URL configuré")
                print_info(f"   {colab_url}")
                checks.append(True)
            else:
                print_warning("COLAB_API_URL ne contient pas 'ngrok'")
                print_info(f"   {colab_url}")
                print_info("Vérifiez que c'est bien l'URL du notebook Colab")
                checks.append(True)
        else:
            print_error("COLAB_API_URL non configuré")
            print_info("Ajoutez: COLAB_API_URL=https://xxxx.ngrok-free.app")
            checks.append(False)
        
        colab_key = os.getenv('COLAB_API_KEY')
        if colab_key:
            if colab_key.startswith('sk-') and len(colab_key) > 20:
                print_success("COLAB_API_KEY configuré")
                print_info(f"   {colab_key[:10]}...{colab_key[-6:]}")
                checks.append(True)
            else:
                print_warning("COLAB_API_KEY format inattendu")
                print_info(f"   {colab_key[:20]}...")
                print_info("Format attendu: sk-xxxxxxxxxxxxxxxx")
                checks.append(True)
        else:
            print_error("COLAB_API_KEY non configuré")
            print_info("Ajoutez: COLAB_API_KEY=sk-xxxxxxxx")
            checks.append(False)
    
    # Vérifier DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print_success("DATABASE_URL configuré")
        checks.append(True)
    else:
        print_error("DATABASE_URL non configuré")
        checks.append(False)
    
    return all(checks)


def check_dependencies():
    """Vérifier les dépendances Python"""
    print_header("Vérification des dépendances")
    
    required_packages = [
        ('httpx', 'httpx'),
        ('dotenv', 'python-dotenv'),
        ('fastapi', 'fastapi'),
        ('sqlalchemy', 'sqlalchemy'),
    ]
    
    all_installed = True
    
    for package_import, package_name in required_packages:
        try:
            __import__(package_import)
            print_success(f"{package_name} installé")
        except ImportError:
            print_error(f"{package_name} manquant")
            print_info(f"   pip install {package_name}")
            all_installed = False
    
    return all_installed


def check_notebook_folder():
    """Vérifier le dossier notebooks"""
    print_header("Vérification du dossier notebooks")
    
    notebooks_dir = Path(__file__).parent.parent / 'notebooks'
    
    if not notebooks_dir.exists():
        print_error("Dossier notebooks/ n'existe pas")
        return False
    
    print_success("Dossier notebooks/ existe")
    
    # Vérifier le notebook
    notebook_file = notebooks_dir / 'colab_inference_server.ipynb'
    if notebook_file.exists():
        size = notebook_file.stat().st_size
        print_success(f"Notebook Colab trouvé ({size / 1024:.1f} KB)")
        
        # Vérifier que c'est un JSON valide
        import json
        try:
            with open(notebook_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cells = data.get('cells', [])
                print_info(f"   {len(cells)} cellules")
                return True
        except json.JSONDecodeError:
            print_error("Le notebook n'est pas un JSON valide")
            return False
    else:
        print_error("colab_inference_server.ipynb manquant")
        return False


def print_next_steps(all_ok):
    """Afficher les prochaines étapes"""
    print_header("Prochaines étapes")
    
    if all_ok:
        print_success("Configuration complète !")
        print("")
        print("Pour démarrer :")
        print("")
        print("1. Ouvrez Google Colab :")
        print("   https://colab.research.google.com/")
        print("")
        print("2. Uploadez le notebook :")
        print("   File → Upload notebook → notebooks/colab_inference_server.ipynb")
        print("")
        print("3. Activez le GPU :")
        print("   Runtime → Change runtime type → T4 GPU")
        print("")
        print("4. Exécutez le notebook :")
        print("   Runtime → Run all")
        print("")
        print("5. Copiez l'URL et la clé API dans backend/.env")
        print("")
        print("6. Testez la connexion :")
        print("   python test_colab_connection.py")
        print("")
        print("📚 Guides disponibles :")
        print("   - QUICK_START_COLAB.md (10 minutes)")
        print("   - GOOGLE_COLAB_SETUP.md (documentation complète)")
        print("")
    else:
        print_error("Configuration incomplète")
        print("")
        print("Corrigez les erreurs ci-dessus, puis relancez ce script.")
        print("")


def main():
    """Fonction principale"""
    print("")
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{'🔍 Validation de la configuration Google Colab':^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    checks = [
        check_files(),
        check_notebook_folder(),
        check_env_config(),
        check_dependencies(),
    ]
    
    all_ok = all(checks)
    
    print_next_steps(all_ok)
    
    if all_ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
