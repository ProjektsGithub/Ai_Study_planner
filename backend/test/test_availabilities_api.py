"""
Test complet de l'API Availabilities
"""
import requests
import json
from datetime import time

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("Test Complet Availabilities API")
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

# 2. Créer une première disponibilité
print("2. Créer une disponibilité (Monday 09:00-12:00)")
availability_data = {
    "day_of_week": "Monday",
    "start_time": "09:00:00",
    "end_time": "12:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=availability_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    avail1 = response.json()
    print(f"   ✓ Disponibilité créée (ID: {avail1['id']})")
    print(f"   - Day: {avail1['day_of_week']}")
    print(f"   - Time: {avail1['start_time']} - {avail1['end_time']}")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 3. Créer une deuxième disponibilité
print("3. Créer une disponibilité (Monday 14:00-18:00)")
availability_data = {
    "day_of_week": "Monday",
    "start_time": "14:00:00",
    "end_time": "18:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=availability_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    avail2 = response.json()
    print(f"   ✓ Disponibilité créée (ID: {avail2['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 4. Créer une troisième disponibilité
print("4. Créer une disponibilité (Wednesday 10:00-16:00)")
availability_data = {
    "day_of_week": "Wednesday",
    "start_time": "10:00:00",
    "end_time": "16:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=availability_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    avail3 = response.json()
    print(f"   ✓ Disponibilité créée (ID: {avail3['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 5. Créer une quatrième disponibilité
print("5. Créer une disponibilité (Friday 08:00-12:00)")
availability_data = {
    "day_of_week": "Friday",
    "start_time": "08:00:00",
    "end_time": "12:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=availability_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    avail4 = response.json()
    print(f"   ✓ Disponibilité créée (ID: {avail4['id']})")
else:
    print(f"   ✗ Erreur: {response.text}")
    exit(1)
print()

# 6. Lister toutes les disponibilités
print("6. Lister toutes les disponibilités")
response = requests.get(f"{BASE_URL}/availabilities", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} disponibilités trouvées")
    for avail in data['availabilities']:
        print(f"   - {avail['day_of_week']}: {avail['start_time']} - {avail['end_time']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 7. Récupérer une disponibilité spécifique
print(f"7. Récupérer la disponibilité Monday 09:00-12:00 (ID: {avail1['id']})")
response = requests.get(f"{BASE_URL}/availabilities/{avail1['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    avail = response.json()
    print(f"   ✓ Disponibilité récupérée: {avail['day_of_week']} {avail['start_time']}-{avail['end_time']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 8. Mettre à jour une disponibilité
print(f"8. Mettre à jour la disponibilité Wednesday (ID: {avail3['id']})")
update_data = {
    "start_time": "09:00:00",
    "end_time": "17:00:00"
}

response = requests.put(f"{BASE_URL}/availabilities/{avail3['id']}", json=update_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    updated = response.json()
    print(f"   ✓ Disponibilité mise à jour")
    print(f"   - Start: {updated['start_time']} (attendu: 09:00:00)")
    print(f"   - End: {updated['end_time']} (attendu: 17:00:00)")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 9. Test de validation - end_time avant start_time
print("9. Test validation - end_time avant start_time")
invalid_data = {
    "day_of_week": "Tuesday",
    "start_time": "14:00:00",
    "end_time": "10:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
    print(f"   - Erreur: {response.json()['detail'][0]['msg']}")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 10. Test de validation - end_time égal à start_time
print("10. Test validation - end_time égal à start_time")
invalid_data = {
    "day_of_week": "Tuesday",
    "start_time": "10:00:00",
    "end_time": "10:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 11. Test de validation - jour invalide
print("11. Test validation - jour invalide")
invalid_data = {
    "day_of_week": "InvalidDay",
    "start_time": "10:00:00",
    "end_time": "12:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 12. Test de validation - format de temps invalide
print("12. Test validation - format de temps invalide")
invalid_data = {
    "day_of_week": "Tuesday",
    "start_time": "25:00:00",
    "end_time": "26:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=invalid_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 422:
    print(f"   ✓ Validation correcte (422 attendu)")
else:
    print(f"   ✗ Erreur: validation devrait échouer")
print()

# 13. Supprimer une disponibilité
print(f"13. Supprimer la disponibilité Friday (ID: {avail4['id']})")
response = requests.delete(f"{BASE_URL}/availabilities/{avail4['id']}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Disponibilité supprimée")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 14. Vérifier la suppression
print("14. Vérifier la suppression")
response = requests.get(f"{BASE_URL}/availabilities", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ {data['total']} disponibilités restantes (attendu: 3)")
    for avail in data['availabilities']:
        print(f"   - {avail['day_of_week']}: {avail['start_time']} - {avail['end_time']}")
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# 15. Test 404 - disponibilité inexistante
print("15. Test 404 - récupérer une disponibilité inexistante")
response = requests.get(f"{BASE_URL}/availabilities/99999", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print(f"   ✓ 404 correct pour disponibilité inexistante")
else:
    print(f"   ✗ Erreur: devrait retourner 404")
print()

# 16. Test des chevauchements autorisés
print("16. Test - chevauchements autorisés sur le même jour")
overlap_data = {
    "day_of_week": "Monday",
    "start_time": "11:00:00",
    "end_time": "15:00:00"
}

response = requests.post(f"{BASE_URL}/availabilities", json=overlap_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    overlap_avail = response.json()
    print(f"   ✓ Chevauchement autorisé (ID: {overlap_avail['id']})")
    print(f"   - Nouvelle: Monday 11:00-15:00")
    print(f"   - Existante: Monday 09:00-12:00")
    print(f"   - Existante: Monday 14:00-18:00")
    # Nettoyage
    requests.delete(f"{BASE_URL}/availabilities/{overlap_avail['id']}", headers=headers)
else:
    print(f"   ✗ Erreur: {response.text}")
print()

# Nettoyage - supprimer les disponibilités restantes
print("17. Nettoyage - supprimer les disponibilités restantes")
requests.delete(f"{BASE_URL}/availabilities/{avail1['id']}", headers=headers)
requests.delete(f"{BASE_URL}/availabilities/{avail2['id']}", headers=headers)
requests.delete(f"{BASE_URL}/availabilities/{avail3['id']}", headers=headers)
print(f"   ✓ Nettoyage terminé")
print()

print("=" * 70)
print("✓ Tous les tests terminés avec succès!")
print("=" * 70)
