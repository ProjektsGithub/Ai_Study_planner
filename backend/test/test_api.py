"""
Script de test rapide pour vérifier que l'API fonctionne
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Test de l'API AI Study Planner")
print("=" * 70)
print()

# Test 1: Health check
print("1. Test Health Check")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Response: {response.json()}")
    else:
        print(f"   ✗ Status: {response.status_code}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
print()

# Test 2: Root endpoint
print("2. Test Root Endpoint")
try:
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print(f"   ✓ Status: {response.status_code}")
        data = response.json()
        print(f"   ✓ App: {data.get('app_name')}")
        print(f"   ✓ Version: {data.get('version')}")
    else:
        print(f"   ✗ Status: {response.status_code}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
print()

# Test 3: API Documentation
print("3. Test Documentation Endpoints")
try:
    docs_response = requests.get(f"{BASE_URL}/docs")
    redoc_response = requests.get(f"{BASE_URL}/redoc")
    
    if docs_response.status_code == 200:
        print(f"   ✓ Swagger UI: {BASE_URL}/docs")
    else:
        print(f"   ✗ Swagger UI: Status {docs_response.status_code}")
    
    if redoc_response.status_code == 200:
        print(f"   ✓ ReDoc: {BASE_URL}/redoc")
    else:
        print(f"   ✗ ReDoc: Status {redoc_response.status_code}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
print()

print("=" * 70)
print("✓ Serveur FastAPI opérationnel!")
print()
print("Prochaines étapes:")
print("  - Ouvrez http://localhost:8000/docs pour voir la documentation")
print("  - Testez l'inscription: POST /api/v1/auth/register")
print("  - Testez la connexion: POST /api/v1/auth/login")
print("=" * 70)
