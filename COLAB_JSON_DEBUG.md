# 🔧 Guide de Débogage - Erreur JSON Colab

## 🎯 Problème

L'erreur `Failed to extract valid JSON from AI response` indique que Llama 3.1-8B sur Colab génère du texte qui n'est pas un JSON valide.

## 📋 Étapes de Diagnostic

### 1. Tester la Génération Colab

```bash
cd backend
python test_colab_generation.py
```

Ce script va :
- ✅ Tester le streaming SSE de Colab
- ✅ Afficher exactement ce que Llama génère
- ✅ Montrer où le JSON est invalide
- ✅ Tester l'endpoint batch pour comparaison

### 2. Problèmes Courants et Solutions

#### A) Llama génère du texte avant le JSON

**Symptôme:** 
```
Here's your study plan:
{
  "sessions": [...]
}
```

**Solution:** Le prompt doit être plus strict. Modifiez `ai_service.py` ligne 150-250 pour ajouter:

```python
# Dans _construct_prompt(), après la ligne "You are an AI study planner..."
CRITICAL: Output ONLY the JSON object. 
- NO explanations before or after
- NO markdown code blocks
- Start IMMEDIATELY with {
- End with }
```

#### B) Llama génère des markdown code blocks

**Symptôme:**
```
```json
{
  "sessions": [...]
}
```
```

**Solution:** Déjà géré par `_extract_json_from_response()`, mais vous pouvez renforcer le prompt:

```python
DO NOT wrap in markdown code blocks.
Output raw JSON directly.
```

#### C) Llama génère des double accolades {{}}

**Symptôme:**
```
{{
  "sessions": [...]
}}
```

**Solution:** Déjà géré par le code (ligne 289 de ai_service.py)

#### D) Llama ne respecte pas le format JSON

**Symptôme:**
```
sessions: [
  day: Monday
  start_time: 09:00
]
```

**Solution:** Le prompt JSON schema doit être plus explicite. Modifiez le prompt pour inclure un exemple concret.

### 3. Vérifier les Logs Backend

Quand l'erreur se produit, regardez la console backend (terminal où `start_backend.bat` tourne):

```
[AI_SERVICE ERROR] Full response:
======================================================================
[Le texte exact généré par Llama sera affiché ici]
======================================================================
```

Cela vous montre EXACTEMENT ce que Llama a généré.

### 4. Solutions Selon le Diagnostic

#### Si le texte généré est vide:
- ❌ Colab n'est pas accessible
- Vérifiez dans Colab que le notebook est actif
- Testez `curl {COLAB_API_URL}/health`

#### Si le texte contient du texte non-JSON:
- 🔧 Renforcez le prompt (voir section 2A ci-dessus)
- 💡 Réduisez `temperature` à 0.05 dans `.env`

#### Si le JSON est malformé (virgules manquantes, etc.):
- 🔧 Ajoutez un exemple JSON complet dans le prompt
- 💡 Augmentez `max_tokens` dans la requête

#### Si Llama génère un format différent:
- 🔧 Modifiez le prompt pour être TRÈS explicite sur le format
- 💡 Ajoutez des exemples de sessions dans le prompt

### 5. Améliorer le Prompt (Solution Rapide)

Ouvrez `backend/app/services/ai_service.py` et modifiez `_construct_prompt()` :

```python
def _construct_prompt(self, ...) -> str:
    # ... code existant ...
    
    prompt = f"""You are an AI study planner assistant.

🚨 CRITICAL OUTPUT RULES:
1. Output ONLY a JSON object
2. NO text before the JSON
3. NO text after the JSON  
4. NO markdown code blocks (no ```)
5. Start immediately with {{
6. End with }}

Example of CORRECT output:
{{
  "sessions": [
    {{
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "subject_id": 1,
      "task_type": "lecture_review",
      "topic": "Calculus - Derivatives"
    }}
  ],
  "total_hours": 1.5,
  "reasoning": "Balanced schedule focusing on priority subjects"
}}

Now generate the study plan based on this data:

**Available Time Slots:**
{json.dumps(planning_data.get('valid_slots', []), indent=2)}

**Subjects (by priority):**
{json.dumps([p for p in planning_data.get('subject_priorities', [])][:5], indent=2)}

**Constraints:**
{json.dumps(planning_data.get('constraints', {{}}), indent=2)}

**Weekly Goal:** {weekly_study_goal} hours

Generate the JSON study plan now (JSON only, no other text):"""

    return prompt
```

### 6. Test Final

Après modifications:

1. Redémarrez le backend: `backend\start_backend.bat`
2. Testez avec: `python test_colab_generation.py`
3. Si OK, testez dans l'interface web

## 📊 Checklist de Vérification

- [ ] Colab notebook est actif (cellule 5 exécutée)
- [ ] `curl {COLAB_API_URL}/health` retourne 200 OK
- [ ] `.env` contient `COLAB_API_URL` et `COLAB_API_KEY` corrects
- [ ] `test_colab_generation.py` génère un JSON valide
- [ ] Les logs backend montrent `[OK] Strategy X succeeded`
- [ ] L'interface web génère le planning sans erreur

## 🆘 Si Rien Ne Fonctionne

### Option 1: Utiliser Ollama Localement (Fallback)

```bash
# Dans .env
AI_SERVICE_TYPE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Option 2: Utiliser un Modèle Plus Petit sur Colab

Dans le notebook Colab, cellule 2, changez:

```python
MODEL_NAME = "unsloth/Llama-3.2-3B-Instruct"  # Plus petit, plus précis
```

Puis: Runtime → Run all

### Option 3: Activer le Mode Debug

Dans `backend/.env`:

```env
LOG_LEVEL=DEBUG
COLAB_DEBUG=true
```

Redémarrez et regardez les logs détaillés.

## 📚 Ressources

- [Documentation Unsloth](https://github.com/unslothai/unsloth)
- [Llama 3.1 Prompt Guide](https://www.llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/)
- [JSON Parsing Strategies](../backend/app/services/ai_service.py#L267)

## ✅ Résolution Typique

Dans 90% des cas, le problème vient de:
1. **Prompt pas assez strict** → Solution: Section 5 ci-dessus
2. **Temperature trop haute** → Solution: `COLAB_TEMPERATURE=0.05`
3. **Max tokens trop bas** → Solution: Augmenter dans le notebook

Testez ces 3 solutions en premier !
