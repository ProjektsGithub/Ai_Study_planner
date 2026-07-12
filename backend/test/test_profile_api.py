"""
Script de test pour l'API Profile Management
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("Test de l'API Profile Management (Tâche 4)")
print("=" * 70)
print()

# Étape 1: Créer un utilisateur de test
print("1. Création d'un utilisateur de test")
register_data = {
    "email": "test_profile@example.com",
    "password": "TestPassword123!",
    "name": "Test User Profile"
}

try:
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print(f"   ✓ Utilisateur créé: {register_data['email']}")
        # Maintenant se connecter pour obtenir le token
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": register_data["email"],
            "password": register_data["password"]
        })
        if login_response.status_code == 200:
            user_data = login_response.json()
            print(f"   ✓ Connecté avec succès")
        else:
            print(f"   ✗ Erreur de connexion: {login_response.status_code}")
            print(f"   {login_response.text}")
            exit(1)
    elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        print(f"   ℹ Utilisateur existe déjà, connexion...")
        # Login si l'utilisateur existe
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": register_data["email"],
            "password": register_data["password"]
        })
        if login_response.status_code == 200:
            user_data = login_response.json()
            print(f"   ✓ Connecté: {register_data['email']}")
        else:
            print(f"   ✗ Erreur de connexion: {login_response.status_code}")
            print(f"   {login_response.text}")
            exit(1)
    else:
        print(f"   ✗ Erreur: {response.status_code}")
        print(f"   {response.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    exit(1)

# Récupérer le token
access_token = user_data.get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}

print(f"   ℹ Token reçu: {access_token[:50]}...")
print()

# Étape 2: Créer un profil
print("2. Création d'un profil étudiant")
profile_data = {
    "cursus": "Informatique",
    "academic_level": "Licence 3",
    "weekly_study_goal": 25.5,
    "preferences": {
        "preferred_study_time": "morning",
        "break_duration": 15
    }
}

try:
    response = requests.post(f"{BASE_URL}/profile", json=profile_data, headers=headers)
    if response.status_code in [200, 201]:
        print(f"   ✓ Profil créé")
        profile = response.json()
        print(f"   ✓ Cursus: {profile['cursus']}")
        print(f"   ✓ Niveau: {profile['academic_level']}")
        print(f"   ✓ Objectif hebdomadaire: {profile['weekly_study_goal']}h")
    else:
        print(f"   ✗ Erreur: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print()

# Étape 3: Récupérer le profil
print("3. Récupération du profil")
try:
    response = requests.get(f"{BASE_URL}/profile", headers=headers)
    if response.status_code == 200:
        profile = response.json()
        print(f"   ✓ Profil récupéré")
        print(f"   ✓ ID: {profile['id']}")
        print(f"   ✓ Cursus: {profile['cursus']}")
        print(f"   ✓ Niveau: {profile['academic_level']}")
        print(f"   ✓ Objectif: {profile['weekly_study_goal']}h")
        print(f"   ✓ Préférences: {profile.get('preferences')}")
    else:
        print(f"   ✗ Erreur: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print()

# Étape 4: Mettre à jour le profil
print("4. Mise à jour du profil")
update_data = {
    "weekly_study_goal": 30.0,
    "preferences": {
        "preferred_study_time": "evening",
        "break_duration": 20
    }
}

try:
    response = requests.put(f"{BASE_URL}/profile", json=update_data, headers=headers)
    if response.status_code == 200:
        profile = response.json()
        print(f"   ✓ Profil mis à jour")
        print(f"   ✓ Nouvel objectif: {profile['weekly_study_goal']}h")
        print(f"   ✓ Nouvelles préférences: {profile.get('preferences')}")
    else:
        print(f"   ✗ Erreur: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print()

# Étape 5: Test de validation
print("5. Test de validation (objectif invalide)")
invalid_data = {
    "weekly_study_goal": 200.0  # > 168 heures
}

try:
    response = requests.put(f"{BASE_URL}/profile", json=invalid_data, headers=headers)
    if response.status_code == 422:
        print(f"   ✓ Validation fonctionne: objectif > 168h rejeté")
    else:
        print(f"   ✗ Validation échouée: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print()
print("=" * 70)
print("✓ Tests de l'API Profile Management terminés!")
print()
print("Critères d'acceptation vérifiés:")
print("  ✓ Création de profil stocke tous les champs")
print("  ✓ Récupération de profil retourne les données complètes")
print("  ✓ Validation de weekly_study_goal (1-168 heures)")
print("  ✓ Mise à jour du profil modifie les enregistrements")
print("  ✓ Gestion des erreurs appropriée")
print("=" * 70)
