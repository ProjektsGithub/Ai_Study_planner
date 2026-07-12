"""
Test direct de la génération JSON avec Colab pour diagnostiquer les problèmes
"""
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

COLAB_API_URL = os.getenv("COLAB_API_URL")
COLAB_API_KEY = os.getenv("COLAB_API_KEY")


async def test_json_generation():
    """Test avec un prompt simple pour voir ce que le modèle génère"""
    
    simple_prompt = """Generate a weekly study schedule in JSON format.

**WEEKLY STUDY GOAL**: 10 hours

**AVAILABLE TIME SLOTS**:
Monday: 09:00-11:00 (120min)
Tuesday: 14:00-16:00 (120min)

**SUBJECTS**:
- Mathematics (priority: 9.0, target: 5h/week)
- Physics (priority: 8.0, target: 5h/week)

**OUTPUT FORMAT** (JSON only, no explanation):
{
  "sessions": [
    {
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Focus on algebra"
    }
  ],
  "total_hours": 10,
  "reasoning": "Schedule optimized"
}

IMPORTANT: Return ONLY valid JSON, no other text before or after. Start with { and end with }.

Generate the study plan now:"""
    
    print("="*70)
    print("TEST DE GÉNÉRATION JSON AVEC COLAB")
    print("="*70)
    print(f"\nURL: {COLAB_API_URL}")
    print(f"API Key: {COLAB_API_KEY[:20]}...")
    print("\n📤 Envoi du prompt...\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{COLAB_API_URL}/generate",
                headers={"Authorization": f"Bearer {COLAB_API_KEY}"},
                json={
                    "prompt": simple_prompt,
                    "temperature": 0.1,  # Très bas pour plus de déterminisme
                    "max_tokens": 800
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('generated_text', '')
                
                print("✅ Génération réussie!")
                print(f"⏱️  Temps: {result.get('generation_time', 0):.2f}s")
                print(f"🔢 Tokens: {result.get('tokens_generated', 0)}")
                print("\n" + "="*70)
                print("RÉPONSE BRUTE DU MODÈLE:")
                print("="*70)
                print(generated_text)
                print("="*70)
                
                # Essayer d'extraire le JSON
                print("\n🔍 EXTRACTION DU JSON...")
                
                # Méthode 1: Code block
                if "```json" in generated_text:
                    start = generated_text.find("```json") + 7
                    end = generated_text.find("```", start)
                    if end != -1:
                        json_str = generated_text[start:end].strip()
                        print("\n✓ JSON trouvé dans code block:")
                        print(json_str)
                        try:
                            data = json.loads(json_str)
                            print("\n✅ JSON VALIDE!")
                            print(f"   Sessions: {len(data.get('sessions', []))}")
                            print(f"   Total heures: {data.get('total_hours', 0)}")
                            return
                        except json.JSONDecodeError as e:
                            print(f"\n❌ JSON invalide: {e}")
                
                # Méthode 2: Entre accolades
                start_idx = generated_text.find("{")
                end_idx = generated_text.rfind("}") + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = generated_text[start_idx:end_idx]
                    print("\n✓ JSON trouvé entre accolades:")
                    print(json_str)
                    try:
                        data = json.loads(json_str)
                        print("\n✅ JSON VALIDE!")
                        print(f"   Sessions: {len(data.get('sessions', []))}")
                        print(f"   Total heures: {data.get('total_hours', 0)}")
                        return
                    except json.JSONDecodeError as e:
                        print(f"\n❌ JSON invalide: {e}")
                
                print("\n❌ IMPOSSIBLE D'EXTRAIRE UN JSON VALIDE")
                print("\n💡 DIAGNOSTIC:")
                print("   Le modèle Llama-3.2-1B-Instruct est trop petit pour cette tâche.")
                print("   Solutions:")
                print("   1. Upgrader vers Llama-3.1-8B-Instruct dans Colab")
                print("   2. Utiliser Colab Pro avec GPU A100")
                print("   3. Simplifier le prompt (moins de contraintes)")
                
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(f"Réponse: {response.text}")
                
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_json_generation())
