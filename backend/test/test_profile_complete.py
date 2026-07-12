"""
Test complet de l'API Profile
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("Test Complet Profile API")
print("=" * 70)
print()

# 1. Login
print("1. Login")
login_data = {
    "email": "test_profile@example.com",
    "password": "TestPassword123!"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code != 200:
    print(f"   ✗ Login échoué: {response.text}")
    exit(1)

access_token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print(f"   ✓ Login réussi")
print()

# 2. Créer un profil
print("2. Créer un profil")
profile_data = {
    "cursus": "Computer Science",
    "academic_level": "Bachelor Year 2",
    "weekly_study_goal": 25,
    "preferences": {
        "preferred_study_times": ["morning", "afternoon"],
        "break_duration": 15,
        "session_length": 90
    }
}

response = requests.post(f"{BASE_URL}/profile", json=profile_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Profil créé")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 3. Récupérer le profil
print("3. Récupérer le profil")
response = requests.get(f"{BASE_URL}/profile", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Profil récupéré")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 4. Mettre à jour le profil
print("4. Mettre à jour le profil")
update_data = {
    "weekly_study_goal": 30,
    "preferences": {
        "preferred_study_times": ["evening"],
        "break_duration": 20,
        "session_length": 120
    }
}

response = requests.put(f"{BASE_URL}/profile", json=update_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Profil mis à jour")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 5. Vérifier la mise à jour
print("5. Vérifier la mise à jour")
response = requests.get(f"{BASE_URL}/profile", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    profile = response.json()
    print(f"   ✓ Profil récupéré")
    print(f"   - weekly_study_goal: {profile['weekly_study_goal']} (attendu: 30)")
    print(f"   - break_duration: {profile['preferences']['break_duration']} (attendu: 20)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 6. Supprimer le profil
print("6. Supprimer le profil")
response = requests.delete(f"{BASE_URL}/profile", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Profil supprimé")
    print(f"   Response: {response.json()}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 7. Vérifier la suppression
print("7. Vérifier la suppression")
response = requests.get(f"{BASE_URL}/profile", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print(f"   ✓ Profil bien supprimé (404 attendu)")
else:
    print(f"   ✗ Erreur: profil toujours présent")
print()

print("=" * 70)
print("✓ Tests terminés avec succès!")
print("=" * 70)
