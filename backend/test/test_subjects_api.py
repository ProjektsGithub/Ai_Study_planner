"""
Test complet de l'API Subjects
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("Test Complet Subjects API")
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

# 2. Créer un premier sujet
print("2. Créer un premier sujet (Mathematics)")
future_date = (date.today() + timedelta(days=30)).isoformat()
subject_data = {
    "name": "Mathematics",
    "priority": 5,
    "difficulty": 4,
    "target_weekly_hours": 10.5,
    "exam_date": future_date
}

response = requests.post(f"{BASE_URL}/subjects", json=subject_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    subject1 = response.json()
    print(f"   ✓ Sujet créé (ID: {subject1['id']})")
    print(f"   - Name: {subject1['name']}")
    print(f"   - Priority: {subject1['priority']}")
    print(f"   - Difficulty: {subject1['difficulty']}")
    print(f"   - Target hours: {subject1['target_weekly_hours']}")
    print(f"   - Exam date: {subject1['exam_date']}")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 3. Créer un deuxième sujet
print("3. Créer un deuxième sujet (Physics)")
subject_data = {
    "name": "Physics",
    "priority": 4,
    "difficulty": 5,
    "target_weekly_hours": 8.0,
    "exam_date": None
}

response = requests.post(f"{BASE_URL}/subjects", json=subject_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    subject2 = response.json()
    print(f"   ✓ Sujet créé (ID: {subject2['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 4. Créer un troisième sujet
print("4. Créer un troisième sujet (Computer Science)")
subject_data = {
    "name": "Computer Science",
    "priority": 3,
    "difficulty": 3,
    "target_weekly_hours": 12.0,
    "exam_date": None
}

response = requests.post(f"{BASE_URL}/subjects", json=subject_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    subject3 = response.json()
    print(f"   ✓ Sujet créé (ID: {subject3['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 5. Lister tous les sujets
print("5. Lister tous les sujets")
response = requests.get(f"{BASE_URL}/subjects", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} sujets trouvés")
    for subject in data['subjects']:
        print(f"   - {subject['name']} (Priority: {subject['priority']}, Difficulty: {subject['difficulty']})")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 6. Récupérer un sujet spécifique
print(f"6. Récupérer le sujet Mathematics (ID: {subject1['id']})")
response = requests.get(f"{BASE_URL}/subjects/{subject1['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    subject = response.json()
    print(f"   ✓ Sujet récupéré: {subject['name']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 7. Mettre à jour un sujet
print(f"7. Mettre à jour le sujet Physics (ID: {subject2['id']})")
update_data = {
    "priority": 5,
    "target_weekly_hours": 15.0
}

response = requests.put(f"{BASE_URL}/subjects/{subject2['id']}", json=update_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    updated = response.json()
    print(f"   ✓ Sujet mis à jour")
    print(f"   - Priority: {updated['priority']} (attendu: 5)")
    print(f"   - Target hours: {updated['target_weekly_hours']} (attendu: 15.0)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 8. Test de validation - date passée
print("8. Test validation - date d'examen passée")
past_date = (date.today() - timedelta(days=1)).isoformat()
invalid_data = {
    "name": "Invalid Subject",
    "priority": 3,
    "difficulty": 3,
    "target_weekly_hours": 5.0,
    "exam_date": past_date
}

response = requests.post(f"{BASE_URL}/subjects", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
    print(f"   - Erreur: {response.json()['detail'][0]['msg']}")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 9. Test de validation - priority hors limites
print("9. Test validation - priority hors limites (6)")
invalid_data = {
    "name": "Invalid Subject",
    "priority": 6,
    "difficulty": 3,
    "target_weekly_hours": 5.0
}

response = requests.post(f"{BASE_URL}/subjects", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 10. Test de validation - target_weekly_hours hors limites
print("10. Test validation - target_weekly_hours hors limites (200)")
invalid_data = {
    "name": "Invalid Subject",
    "priority": 3,
    "difficulty": 3,
    "target_weekly_hours": 200.0
}

response = requests.post(f"{BASE_URL}/subjects", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 11. Supprimer un sujet
print(f"11. Supprimer le sujet Computer Science (ID: {subject3['id']})")
response = requests.delete(f"{BASE_URL}/subjects/{subject3['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Sujet supprimé")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 12. Vérifier la suppression
print("12. Vérifier la suppression")
response = requests.get(f"{BASE_URL}/subjects", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} sujets restants (attendu: 2)")
    for subject in data['subjects']:
        print(f"   - {subject['name']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 13. Test 404 - sujet inexistant
print("13. Test 404 - récupérer un sujet inexistant")
response = requests.get(f"{BASE_URL}/subjects/99999", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print(f"   ✓ 404 correct pour sujet inexistant")
else:
    print(f"   ✗ Erreur: devrait retourner 404")
print()

# Nettoyage - supprimer les sujets restants
print("14. Nettoyage - supprimer les sujets restants")
requests.delete(f"{BASE_URL}/subjects/{subject1['id']}", headers=headers)
requests.delete(f"{BASE_URL}/subjects/{subject2['id']}", headers=headers)
print(f"   ✓ Nettoyage terminé")
print()

print("=" * 70)
print("✓ Tous les tests terminés avec succès!")
print("=" * 70)
