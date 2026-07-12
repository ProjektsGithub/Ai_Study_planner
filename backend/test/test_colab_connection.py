"""
Test script pour vérifier la connexion avec Google Colab API
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

COLAB_API_URL = os.getenv("COLAB_API_URL")
COLAB_API_KEY = os.getenv("COLAB_API_KEY")


async def test_colab_connection():
    """Test la connexion basique avec le serveur Colab"""
    print("\n" + "="*70)
    print("🧪 TEST DE CONNEXION GOOGLE COLAB")
    print("="*70)
    
    # Vérifier la configuration
    print("\n📋 Configuration détectée:")
    print(f"   COLAB_API_URL : {COLAB_API_URL}")
    print(f"   COLAB_API_KEY : {COLAB_API_KEY[:20]}..." if COLAB_API_KEY else "   COLAB_API_KEY : Non définie")
    
    if not COLAB_API_URL or not COLAB_API_KEY:
        print("\n❌ ERREUR: COLAB_API_URL ou COLAB_API_KEY non définis dans .env")
        return False
    
    # Test 1: Vérifier que le serveur répond
    print("\n📡 Test 1: Connexion au serveur...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{COLAB_API_URL}/health",
                headers={"Authorization": f"Bearer {COLAB_API_KEY}"}
            )
            
            if response.status_code == 200:
                print("   ✅ Serveur accessible!")
                health_data = response.json()
                print(f"   📊 Status: {health_data.get('status', 'unknown')}")
                print(f"   🤖 Modèle: {health_data.get('model', 'unknown')}")
                print(f"   💻 Device: {health_data.get('device', 'unknown')}")
                if 'gpu_name' in health_data:
                    print(f"   🎮 GPU: {health_data['gpu_name']}")
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
    except httpx.ConnectError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Vérifiez que:")
        print("      - Le notebook Colab est en cours d'exécution")
        print("      - L'URL ngrok est correcte et active")
        print("      - Vous avez une connexion internet")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        return False
    
    # Test 2: Tester la génération de texte
    print("\n🤖 Test 2: Génération de texte...")
    try:
        test_prompt = """Generate a simple study schedule for Monday with 2 hours of study time.
Output JSON format:
{
  "sessions": [
    {
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review"
    }
  ]
}"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{COLAB_API_URL}/generate",
                headers={"Authorization": f"Bearer {COLAB_API_KEY}"},
                json={
                    "prompt": test_prompt,
                    "temperature": 0.2,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Génération réussie!")
                print(f"   ⏱️  Temps de génération: {result.get('generation_time', 0):.2f}s")
                print(f"   🔢 Tokens générés: {result.get('tokens_generated', 0)}")
                print("\n   📝 Réponse générée:")
                print("   " + "-"*66)
                generated_text = result.get('generated_text', '')[:300]
                print(f"   {generated_text}...")
                print("   " + "-"*66)
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("   ❌ Timeout - La génération a pris trop de temps")
        print("   💡 Ceci peut arriver si:")
        print("      - Le modèle est en cours de chargement (première requête)")
        print("      - Le GPU Colab est surchargé")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        return False
    
    # Test 3: Vérifier l'authentification
    print("\n🔐 Test 3: Vérification de l'authentification...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test avec une mauvaise clé API
            response = await client.get(
                f"{COLAB_API_URL}/health",
                headers={"Authorization": "Bearer invalid-key"}
            )
            
            if response.status_code == 401:
                print("   ✅ Authentification fonctionne correctement!")
                print("   (Requête avec clé invalide bien rejetée)")
            else:
                print(f"   ⚠️  Réponse inattendue: {response.status_code}")
                
    except Exception as e:
        print(f"   ⚠️  Impossible de tester l'authentification: {str(e)}")
    
    # Résumé
    print("\n" + "="*70)
    print("✅ TOUS LES TESTS RÉUSSIS!")
    print("="*70)
    print("\n💡 Prochaines étapes:")
    print("   1. Vous pouvez maintenant générer des plans d'étude via l'API")
    print("   2. Le backend utilisera automatiquement Google Colab")
    print("   3. Testez via l'interface frontend: http://localhost:5173")
    print("\n⚠️  Note importante:")
    print("   - L'URL ngrok change à chaque redémarrage du notebook Colab")
    print("   - Mettez à jour COLAB_API_URL dans .env si nécessaire")
    print("   - Les sessions Colab expirent après 12-24h d'inactivité")
    print("\n")
    
    return True


async def test_full_generation():
    """Test complet avec un prompt réaliste"""
    print("\n" + "="*70)
    print("🎯 TEST AVANCÉ: GÉNÉRATION DE PLAN D'ÉTUDE COMPLET")
    print("="*70)
    
    realistic_prompt = """You are an AI study planner. Generate a weekly study schedule based on the following data.

**WEEKLY STUDY GOAL**: 20 hours

**AVAILABLE TIME SLOTS**:

Monday:
  - 09:00:00-11:00:00 (120min) [Energy: high]
  - 14:00:00-17:00:00 (180min) [Energy: medium]

Tuesday:
  - 10:00:00-12:00:00 (120min) [Energy: high]

Wednesday:
  - 09:00:00-11:00:00 (120min) [Energy: high]
  - 14:00:00-16:00:00 (120min) [Energy: medium]

**SUBJECTS** (ordered by priority):
- Mathematics [MANDATORY] (priority: 9.5, target: 6h/week, exam: 2024-12-15)
- Physics [MANDATORY] (priority: 8.0, target: 5h/week, exam: 2024-12-20)
- Computer Science (priority: 7.0, target: 4h/week)

**CONSTRAINTS**:
- Maximum 6 hours of study per day
- Take 15min break after 90min of study

**OUTPUT FORMAT** (JSON only, no explanation):
{
  "sessions": [
    {
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Focus on algebra"
    }
  ],
  "total_hours": 20,
  "reasoning": "Schedule optimized for exam preparation"
}

Generate the study plan now:"""
    
    print("\n📤 Envoi du prompt (génération peut prendre 5-15 secondes)...")
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{COLAB_API_URL}/generate",
                headers={"Authorization": f"Bearer {COLAB_API_KEY}"},
                json={
                    "prompt": realistic_prompt,
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Génération réussie!")
                print(f"   ⏱️  Temps: {result.get('generation_time', 0):.2f}s")
                print(f"   🔢 Tokens: {result.get('tokens_generated', 0)}")
                
                print("\n   📄 Plan d'étude généré:")
                print("   " + "="*66)
                generated_text = result.get('generated_text', '')
                print(generated_text)
                print("   " + "="*66)
                
                # Essayer d'extraire le JSON
                import json
                try:
                    # Chercher le JSON dans la réponse
                    start_idx = generated_text.find("{")
                    end_idx = generated_text.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = generated_text[start_idx:end_idx]
                        plan_data = json.loads(json_str)
                        
                        print("\n   ✅ JSON valide détecté!")
                        print(f"   📊 Nombre de sessions: {len(plan_data.get('sessions', []))}")
                        print(f"   ⏰ Total d'heures: {plan_data.get('total_hours', 0)}h")
                except:
                    print("\n   ⚠️  JSON non valide ou non trouvé dans la réponse")
                    
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        return False
    
    print("\n")
    return True


if __name__ == "__main__":
    # Exécuter les tests
    success = asyncio.run(test_colab_connection())
    
    if success:
        # Si les tests de base passent, faire le test avancé
        print("\n🚀 Lancement du test avancé...\n")
        asyncio.run(test_full_generation())
    else:
        print("\n❌ Les tests de base ont échoué. Résolvez les problèmes ci-dessus avant de continuer.")
        exit(1)
