"""
Script de diagnostic rapide pour voir ce que Colab génère
AVEC la nouvelle stratégie d'extraction
"""
import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

COLAB_URL = os.getenv('COLAB_API_URL')
COLAB_KEY = os.getenv('COLAB_API_KEY')

def extract_json_smart(response_text):
    """
    Extraction intelligente : trouve le premier objet JSON complet
    et ignore tout ce qui suit
    """
    import json
    import re
    
    # Nettoyage basique
    text = re.sub(r'```json\s*', '', response_text)
    text = re.sub(r'```\s*', '', text)
    text = text.replace('{{', '{').replace('}}', '}')
    
    # Stratégie: compter les accolades pour trouver l'objet JSON complet
    start_idx = text.find("{")
    if start_idx == -1:
        return None, "Pas de { trouvé"
    
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start_idx, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
        elif char == '{' and not in_string:
            depth += 1
        elif char == '}' and not in_string:
            depth -= 1
            if depth == 0:
                # Objet JSON complet trouvé !
                json_str = text[start_idx:i+1]
                try:
                    return json.loads(json_str), None
                except json.JSONDecodeError as e:
                    return None, f"JSON invalide: {e}"
    
    return None, "Pas de fermeture de l'objet JSON"

async def test():
    if not COLAB_URL:
        print("❌ COLAB_API_URL non défini dans .env")
        return
    
    print(f"🔍 Test Colab: {COLAB_URL}")
    print()
    
    # Test simple
    prompt = """You are a study planner. Generate ONLY this JSON (no other text):
{"sessions":[{"day":"Monday","start_time":"09:00:00","end_time":"10:00:00","subject_name":"Math","task_type":"lecture_review","notes":"Test"}],"total_hours":1.0,"reasoning":"Test"}

Generate:"""

    try:
        headers = {"Authorization": f"Bearer {COLAB_KEY}"} if COLAB_KEY else {}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("📤 Test /generate (batch)...")
            resp = await client.post(
                f"{COLAB_URL}/generate",
                json={"prompt": prompt, "temperature": 0.1, "max_tokens": 300},
                headers=headers
            )
            
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("generated_text", "")
                print(f"✅ Réponse reçue ({len(text)} chars)")
                print()
                print("📝 Texte généré:")
                print("="*70)
                print(text)
                print("="*70)
                print()
                
                # Utiliser la nouvelle stratégie d'extraction
                result, error = extract_json_smart(text)
                
                if result:
                    print("✅ JSON EXTRAIT AVEC SUCCÈS!")
                    import json
                    print(json.dumps(result, indent=2))
                else:
                    print(f"❌ Échec extraction: {error}")
            else:
                print(f"❌ Erreur HTTP {resp.status_code}")
                print(resp.text)
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
