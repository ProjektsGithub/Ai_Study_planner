"""
Test simple de génération AI pour déboguer le problème de JSON vide
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

COLAB_API_URL = os.getenv("COLAB_API_URL")
COLAB_API_KEY = os.getenv("COLAB_API_KEY")

async def test_simple_generation():
    """Test avec un prompt ultra simple"""
    
    # Prompt très simple et direct
    simple_prompt = """Generate a study schedule in JSON format.

Output ONLY this JSON structure (no other text):
{
  "sessions": [
    {
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "11:00:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Review calculus"
    }
  ],
  "total_hours": 2.0,
  "reasoning": "Simple schedule"
}

Generate the JSON now (start with { and end with }):"""
    
    print("=" * 70)
    print("🧪 TEST SIMPLE DE GÉNÉRATION AI")
    print("=" * 70)
    print(f"\n📤 Envoi du prompt à Colab...")
    print(f"   URL: {COLAB_API_URL}")
    print(f"   Prompt length: {len(simple_prompt)} characters")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{COLAB_API_URL}/generate",
                headers={"Authorization": f"Bearer {COLAB_API_KEY}"},
                json={
                    "prompt": simple_prompt,
                    "temperature": 0.1,  # Plus bas = plus déterministe
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('generated_text', '')
                
                print(f"\n✅ Génération réussie en {result.get('generation_time', 0):.2f}s")
                print(f"   Tokens générés: {result.get('tokens_generated', 0)}")
                print(f"\n📄 RÉPONSE BRUTE (longueur: {len(generated_text)} chars):")
                print("=" * 70)
                print(generated_text)
                print("=" * 70)
                
                # Essayer de parser le JSON
                import json
                try:
                    # Chercher le JSON dans la réponse
                    start_idx = generated_text.find("{")
                    end_idx = generated_text.rfind("}") + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = generated_text[start_idx:end_idx]
                        plan_data = json.loads(json_str)
                        
                        print(f"\n✅ JSON VALIDE EXTRAIT!")
                        print(f"   Nombre de sessions: {len(plan_data.get('sessions', []))}")
                        print(f"   Total heures: {plan_data.get('total_hours', 0)}h")
                        
                        if plan_data.get('sessions'):
                            print(f"\n📅 Sessions:")
                            for sess in plan_data['sessions']:
                                print(f"   - {sess['day']} {sess['start_time']}-{sess['end_time']}: {sess['subject_name']}")
                    else:
                        print(f"\n❌ Pas de JSON trouvé dans la réponse")
                        
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON invalide: {e}")
                    print(f"   Extrait tenté: {json_str[:200]}...")
                    
            else:
                print(f"\n❌ Erreur HTTP {response.status_code}")
                print(f"   Réponse: {response.text}")
                
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_generation())
