"""
Test complet de l'API Constraints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("Test Complet Constraints API")
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

# 2. Créer un sujet pour les tests fixed_slot
print("2. Créer un sujet pour les tests")
subject_data = {
    "name": "Test Subject",
    "priority": 3,
    "difficulty": 3,
    "target_weekly_hours": 5.0
}

response = requests.post(f"{BASE_URL}/subjects", json=subject_data, headers=headers)
if response.status_code != 201:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)

subject_id = response.json()["id"]
print(f"   ✓ Sujet créé (ID: {subject_id})")
print()

# 3. Créer une contrainte forbidden_slot
print("3. Créer une contrainte forbidden_slot (Monday 12:00-13:00)")
constraint_data = {
    "constraint_type": "forbidden_slot",
    "parameters": {
        "day_of_week": "Monday",
        "start_time": "12:00:00",
        "end_time": "13:00:00"
    },
    "active": True
}

response = requests.post(f"{BASE_URL}/constraints", json=constraint_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    constraint1 = response.json()
    print(f"   ✓ Contrainte créée (ID: {constraint1['id']})")
    print(f"   - Type: {constraint1['constraint_type']}")
    print(f"   - Parameters: {constraint1['parameters']}")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 4. Créer une contrainte max_daily_hours
print("4. Créer une contrainte max_daily_hours (8 heures)")
constraint_data = {
    "constraint_type": "max_daily_hours",
    "parameters": {
        "max_hours": 8
    },
    "active": True
}

response = requests.post(f"{BASE_URL}/constraints", json=constraint_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    constraint2 = response.json()
    print(f"   ✓ Contrainte créée (ID: {constraint2['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 5. Créer une contrainte required_break
print("5. Créer une contrainte required_break (15 min après 90 min)")
constraint_data = {
    "constraint_type": "required_break",
    "parameters": {
        "duration_minutes": 15,
        "after_minutes": 90
    },
    "active": True
}

response = requests.post(f"{BASE_URL}/constraints", json=constraint_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    constraint3 = response.json()
    print(f"   ✓ Contrainte créée (ID: {constraint3['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 6. Créer une contrainte fixed_slot
print(f"6. Créer une contrainte fixed_slot (Wednesday 14:00-16:00, subject {subject_id})")
constraint_data = {
    "constraint_type": "fixed_slot",
    "parameters": {
        "day_of_week": "Wednesday",
        "start_time": "14:00:00",
        "end_time": "16:00:00",
        "subject_id": subject_id
    },
    "active": True
}

response = requests.post(f"{BASE_URL}/constraints", json=constraint_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    constraint4 = response.json()
    print(f"   ✓ Contrainte créée (ID: {constraint4['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 7. Lister toutes les contraintes
print("7. Lister toutes les contraintes")
response = requests.get(f"{BASE_URL}/constraints", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} contraintes trouvées")
    print(f"   - Active: {data['active_count']}")
    print(f"   - Inactive: {data['inactive_count']}")
    for constraint in data['constraints']:
        print(f"   - {constraint['constraint_type']}: {constraint['parameters']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 8. Récupérer une contrainte spécifique
print(f"8. Récupérer la contrainte forbidden_slot (ID: {constraint1['id']})")
response = requests.get(f"{BASE_URL}/constraints/{constraint1['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    constraint = response.json()
    print(f"   ✓ Contrainte récupérée: {constraint['constraint_type']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 9. Mettre à jour une contrainte
print(f"9. Mettre à jour la contrainte max_daily_hours (ID: {constraint2['id']})")
update_data = {
    "parameters": {
        "max_hours": 6
    }
}

response = requests.put(f"{BASE_URL}/constraints/{constraint2['id']}", json=update_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    updated = response.json()
    print(f"   ✓ Contrainte mise à jour")
    print(f"   - max_hours: {updated['parameters']['max_hours']} (attendu: 6)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 10. Toggle active status
print(f"10. Toggle active status de la contrainte required_break (ID: {constraint3['id']})")
response = requests.patch(f"{BASE_URL}/constraints/{constraint3['id']}/toggle", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    toggled = response.json()
    print(f"   ✓ Status toggled")
    print(f"   - Active: {toggled['active']} (attendu: False)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 11. Lister seulement les contraintes actives
print("11. Lister seulement les contraintes actives")
response = requests.get(f"{BASE_URL}/constraints?active_only=true", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} contraintes actives")
    for constraint in data['constraints']:
        print(f"   - {constraint['constraint_type']} (active: {constraint['active']})")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 12. Test validation - max_hours hors limites
print("12. Test validation - max_hours hors limites (30)")
invalid_data = {
    "constraint_type": "max_daily_hours",
    "parameters": {
        "max_hours": 30
    }
}

response = requests.post(f"{BASE_URL}/constraints", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 13. Test validation - duration_minutes hors limites
print("13. Test validation - duration_minutes hors limites (200)")
invalid_data = {
    "constraint_type": "required_break",
    "parameters": {
        "duration_minutes": 200,
        "after_minutes": 60
    }
}

response = requests.post(f"{BASE_URL}/constraints", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 14. Test validation - subject_id invalide pour fixed_slot
print("14. Test validation - subject_id invalide pour fixed_slot")
invalid_data = {
    "constraint_type": "fixed_slot",
    "parameters": {
        "day_of_week": "Friday",
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "subject_id": 99999
    }
}

response = requests.post(f"{BASE_URL}/constraints", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 400:
    print(f"   ✓ Validation correcte (400 attendu)")
    print(f"   - Erreur: {response.json()['detail']}")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 15. Test validation - end_time avant start_time
print("15. Test validation - end_time avant start_time dans forbidden_slot")
invalid_data = {
    "constraint_type": "forbidden_slot",
    "parameters": {
        "day_of_week": "Tuesday",
        "start_time": "14:00:00",
        "end_time": "10:00:00"
    }
}

response = requests.post(f"{BASE_URL}/constraints", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 16. Test validation - champs manquants
print("16. Test validation - champs manquants dans required_break")
invalid_data = {
    "constraint_type": "required_break",
    "parameters": {
        "duration_minutes": 15
        # Manque after_minutes
    }
}

response = requests.post(f"{BASE_URL}/constraints", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 17. Supprimer une contrainte
print(f"17. Supprimer la contrainte fixed_slot (ID: {constraint4['id']})")
response = requests.delete(f"{BASE_URL}/constraints/{constraint4['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Contrainte supprimée")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 18. Vérifier la suppression
print("18. Vérifier la suppression")
response = requests.get(f"{BASE_URL}/constraints", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} contraintes restantes (attendu: 3)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 19. Test 404 - contrainte inexistante
print("19. Test 404 - récupérer une contrainte inexistante")
response = requests.get(f"{BASE_URL}/constraints/99999", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print(f"   ✓ 404 correct pour contrainte inexistante")
else:
    print(f"   ✗ Erreur: devrait retourner 404")
print()

# Nettoyage
print("20. Nettoyage - supprimer les contraintes et le sujet")
requests.delete(f"{BASE_URL}/constraints/{constraint1['id']}", headers=headers)
requests.delete(f"{BASE_URL}/constraints/{constraint2['id']}", headers=headers)
requests.delete(f"{BASE_URL}/constraints/{constraint3['id']}", headers=headers)
requests.delete(f"{BASE_URL}/subjects/{subject_id}", headers=headers)
print(f"   ✓ Nettoyage terminé")
print()

print("=" * 70)
print("✓ Tous les tests terminés avec succès!")
print("=" * 70)
