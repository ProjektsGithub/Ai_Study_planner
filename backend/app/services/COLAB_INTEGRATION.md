# 🔌 Intégration Google Colab - AI Service

## Vue d'ensemble

Le `ai_service.py` supporte deux backends :

1. **Ollama** (local, développement)
2. **Google Colab** (production, GPU distant)

---

## Architecture

```python
┌─────────────────────────────────────────────────────────┐
│                    AIService                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  __init__(db: Session)                         │  │
│  │  • Lit AI_SERVICE_TYPE depuis .env             │  │
│  │  • Configure base_url et api_key               │  │
│  └─────────────────────────────────────────────────┘  │
│                          │                              │
│                          ▼                              │
│         ┌────────────────────────────┐                 │
│         │  AI_SERVICE_TYPE ?         │                 │
│         └────────────────────────────┘                 │
│              │                    │                     │
│         "ollama"             "colab"                    │
│              │                    │                     │
│              ▼                    ▼                     │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ _call_ollama_api │  │ _call_colab_api  │          │
│  │                  │  │                  │          │
│  │ POST /api/gen... │  │ POST /generate   │          │
│  │ • No auth        │  │ • Bearer token   │          │
│  │ • LoRA option    │  │ • LoRA support   │          │
│  └──────────────────┘  └──────────────────┘          │
│              │                    │                     │
│              └─────────┬──────────┘                     │
│                        ▼                                │
│         ┌───────────────────────────┐                  │
│         │  _extract_json_from_res.. │                  │
│         │  • Parse JSON from text   │                  │
│         │  • Handle code blocks     │                  │
│         └───────────────────────────┘                  │
│                        │                                │
│                        ▼                                │
│              ┌─────────────────┐                       │
│              │  GenerationLog  │                       │
│              │  • Track stats  │                       │
│              │  • Store errors │                       │
│              └─────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration (.env)

### **Mode Ollama (local)**

```bash
AI_SERVICE_TYPE=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.2
OLLAMA_NUM_CTX=4096
OLLAMA_TIMEOUT=30
```

### **Mode Colab (production)**

```bash
AI_SERVICE_TYPE=colab
COLAB_API_URL=https://xxxx-xx-xx.ngrok-free.app
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.2
OLLAMA_NUM_CTX=4096
OLLAMA_TIMEOUT=60  # Plus long pour Colab
```

---

## API Endpoints

### **Colab Flask Server**

#### **GET /health**
Vérifier l'état du serveur (pas d'auth requise)

**Response:**
```json
{
  "status": "healthy",
  "model": "meta-llama/Llama-3.2-3B-Instruct",
  "device": "cuda",
  "gpu": "Tesla T4",
  "stats": {
    "requests_count": 42,
    "total_tokens": 12345,
    "avg_generation_time": 2.34,
    "start_time": "2024-06-10T12:00:00"
  }
}
```

#### **POST /generate**
Générer du texte (auth requise)

**Headers:**
```
Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

**Request:**
```json
{
  "prompt": "Your prompt here",
  "temperature": 0.2,
  "max_tokens": 1024
}
```

**Response:**
```json
{
  "generated_text": "Generated text...",
  "generation_time": 2.34,
  "tokens_generated": 156
}
```

#### **GET /stats**
Obtenir les statistiques (auth requise)

**Response:**
```json
{
  "requests_count": 42,
  "total_tokens": 12345,
  "avg_generation_time": 2.34,
  "start_time": "2024-06-10T12:00:00"
}
```

---

## Code Client (ai_service.py)

### **Initialisation**

```python
# Automatique selon AI_SERVICE_TYPE
service = AIService(db)

# Le constructeur configure automatiquement :
if settings.AI_SERVICE_TYPE == 'colab':
    service.base_url = settings.COLAB_API_URL
    service.api_key = settings.COLAB_API_KEY
else:
    service.base_url = settings.OLLAMA_BASE_URL
    service.api_key = None
```

### **Appel Colab**

```python
async def _call_colab_api(self, prompt: str) -> Dict[str, Any]:
    url = f"{self.base_url}/generate"
    
    headers = {}
    if self.api_key:
        headers["Authorization"] = f"Bearer {self.api_key}"
    
    payload = {
        "prompt": prompt,
        "temperature": self.temperature,
        "max_tokens": self.num_ctx,
    }
    
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

### **Génération de plan**

```python
result = await ai_service.generate_study_plan(
    planning_data=planning_data,
    weekly_study_goal=25.0,
    user_preferences={"session_length": 90},
    user_id=1,
    profile_context={"semester_start_date": "2024-09-01"}
)

if result["success"]:
    plan = result["plan"]
    sessions = plan["sessions"]
    # Utiliser les sessions...
else:
    error = result["error"]
    # Gérer l'erreur...
```

---

## Gestion des erreurs

### **Timeout**

```python
except httpx.TimeoutException:
    # Colab trop lent ou déconnecté
    return {
        "success": False,
        "error": "AI service timeout",
        "log_id": log.id
    }
```

### **401 Unauthorized**

```python
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        # Clé API invalide
        return {
            "success": False,
            "error": "Invalid API key",
            "log_id": log.id
        }
```

### **Connection Error**

```python
except httpx.ConnectError:
    # Colab non accessible (URL incorrecte, notebook arrêté)
    return {
        "success": False,
        "error": "Cannot connect to AI service",
        "log_id": log.id
    }
```

---

## Logging

Toutes les générations sont loggées dans `generation_log` :

```python
log = GenerationLog(
    user_id=user_id,
    request_hash=request_hash,  # SHA-256 du prompt
    success=True/False,
    duration_seconds=2.34,
    token_count=156,
    error_message=None or str(error),
    created_at=datetime.now(timezone.utc)
)
```

**Utilité :**
- Debugging
- Analyse de performance
- Coût monitoring
- Détection de patterns d'erreurs

---

## Tests

### **Test unitaire**

```python
import pytest
from app.services.ai_service import AIService

@pytest.mark.asyncio
async def test_colab_generation(db_session):
    service = AIService(db_session)
    
    # Mock planning data
    planning_data = {...}
    
    result = await service.generate_study_plan(
        planning_data=planning_data,
        weekly_study_goal=25.0,
        user_preferences={},
        user_id=1
    )
    
    assert result["success"] == True
    assert "sessions" in result["plan"]
```

### **Test d'intégration**

```bash
# Test de connexion complet
cd backend
python test_colab_connection.py
```

---

## Migration d'Ollama vers Colab

### **Étape 1 : Configurer Colab**

1. Uploadez `notebooks/colab_inference_server.ipynb` dans Colab
2. Runtime → Run all
3. Copiez l'URL ngrok et la clé API

### **Étape 2 : Mettre à jour .env**

```bash
# Avant (Ollama)
AI_SERVICE_TYPE=ollama

# Après (Colab)
AI_SERVICE_TYPE=colab
COLAB_API_URL=https://xxxx.ngrok-free.app
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### **Étape 3 : Redémarrer le backend**

```bash
# Ctrl+C pour arrêter uvicorn
python -m uvicorn app.main:app --reload
```

**C'est tout !** Le changement est automatique.

---

## Fallback automatique

Pour implémenter un fallback automatique (Colab → Ollama) :

```python
async def generate_study_plan(...):
    # Essayer Colab d'abord
    if self.use_colab:
        try:
            return await self._call_colab_api(prompt)
        except Exception as e:
            logger.warning(f"Colab failed: {e}, falling back to Ollama")
            # Fallback vers Ollama
            self.use_colab = False
            return await self._call_ollama_api(prompt)
    else:
        return await self._call_ollama_api(prompt)
```

*(Non implémenté actuellement, mais facilement ajoutable)*

---

## Performances

### **Ollama (local)**
- Latence : ~2-5s (GPU) / ~10-30s (CPU)
- Coût : 0€
- Disponibilité : 100%

### **Colab Free**
- Latence : ~3-5s
- Coût : 0€
- Disponibilité : ~80% (sessions limitées)

### **Colab Pro**
- Latence : ~1-3s (A100)
- Coût : 10€/mois
- Disponibilité : ~95%

---

## Sécurité

### **Clé API**

- Format : `sk-{48 caractères aléatoires}`
- Génération : `secrets.token_urlsafe(32)`
- Stockage : `.env` (Git ignored)
- Transmission : Header `Authorization: Bearer`

### **HTTPS**

- Ngrok fournit automatiquement HTTPS (SSL/TLS)
- Certificats valides
- Pas de configuration supplémentaire

### **Rate Limiting**

À implémenter dans le backend :

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.headers.get("X-Forwarded-For"))

@app.post("/api/v1/study-plans/generate")
@limiter.limit("10/minute")
async def generate_plan(...):
    ...
```

---

## Monitoring

### **Métriques à surveiller**

- Temps de réponse moyen
- Taux d'erreur (%)
- Nombre de requêtes/heure
- Token usage
- Coût estimé

### **Dashboard Colab**

Le notebook affiche en temps réel :
- 📊 Nombre de requêtes
- ⏱️ Temps moyen de génération
- 🔢 Tokens générés
- ❌ Erreurs

---

## Troubleshooting

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Timeout après 30s | Colab lent/arrêté | Augmenter `OLLAMA_TIMEOUT` à 60s |
| 401 Unauthorized | Clé API incorrecte | Vérifier `COLAB_API_KEY` |
| Connection refused | URL incorrecte | Mettre à jour `COLAB_API_URL` |
| JSON parse error | Format de réponse invalide | Vérifier les prompts |
| Session expired | Colab inactif > 12h | Relancer le notebook |

---

## Roadmap

- [ ] Fallback automatique Colab → Ollama
- [ ] Cache de génération (Redis)
- [ ] Support LoRA adapters
- [ ] Batch processing
- [ ] Retry avec backoff exponentiel
- [ ] Métriques Prometheus
- [ ] Circuit breaker pattern

