"""
Chat endpoint — AI assistant chatbot powered by Colab/Llama

Key design:
- Minimal instruction-style prompt (no ### headers that trigger hallucination loops)
- max_tokens capped at 350 for chat
- Post-processing strips repeated fake conversation
- /chat/health endpoint for quick diagnosis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import re
import time
import httpx

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

CHAT_MAX_TOKENS = 350

# Patterns indicating the model generated end-of-turn or hallucinated self-dialogue
_STOP_PATTERNS = [
    # Special tokens (Llama, HuggingFace)
    r"<\|(?:eot_id|start_header_id|end_header_id|reserved_special_token)[^>]*>",
    r"\[\/?(?:INST|SYS)\]",
    r"<\/s>|<s>",
    # Delimiters
    r"\n---|\n===",
    r"\n###\s+(?:QUESTION|HISTORIQUE|FIN|NOTE|MESSAGE|CONTEXTE|PROGRESSION|EMPLOI|INSTRUCTION|REPONSE)",
    # Simulated student or user turns (must be preceded by a newline to avoid false positives at start)
    r"\n\s*[-*•]?\s*(?:\d+[\.\)])?\s*(?:\*\*)?(?:Étudiant|Étudent|Student|User|Utilisateur|Élève|Client)\s*(?:\*\*)?\s*:",
    r"\n\s*\[(?:Étudiant|Étudent|Student|User|Utilisateur|Élève)\]\s*:?",
    # Simulated assistant turns (when model generates another self-turn)
    r"\n\s*[-*•]?\s*(?:\d+[\.\)])?\s*(?:\*\*)?(?:Assistant|Toi|Chatbot|Bot|AI|Conseiller)\s*(?:\*\*)?\s*:",
    r"\n\s*\[(?:Assistant|Chatbot|Bot|AI)\]\s*:?",
    # Section meta-labels
    r"\n\s*[-*•]?\s*(?:\*\*)?(?:Question(?:\s+suivante|\s+de\s+l'étudiant)?|Prochaine\s+question|Nouvelle\s+question|Dialogue\s+suivant)\s*(?:\*\*)?\s*:",
    r"(?:\n|\s+)(?:Réponse\s+MUST|Réponse\s+générée|Réponse\s+JUSTIFIÉE|Réponse\s+finale|Réponse\s+définitive|Réponse\s+justifiée|JUSTIFIÉE|Justification\s*:|Synthèse\s*:|Conclusion\s*:|Résultat\s*:)",
    # End markers
    r"###\s*FIN|\[FIN\]|fin\s+de\s+(?:la|le)\s+session|note\s+de\s+l['\’]assistant",
    r"(?:Veux-tu\s+ajouter|Pour\s+.+\s+tu\s+devrais\s+peut-être|il\s+faudrait\s+peut-être|tu\s+peux\s+peut-être\s+me\s+demander)",
]
_STOP_RE = re.compile("|".join(_STOP_PATTERNS), re.IGNORECASE)


def _truncate_hallucination(text: str) -> str:
    # First truncate at the earliest detected turn / hallucination sequence
    m = _STOP_RE.search(text)
    if m:
        text = text[: m.start()].rstrip()
    
    # Strip residual header / role prefixes if generated at the very beginning of the response
    text = re.sub(
        r"^\s*[-*•]?\s*(?:\*\*)?(?:Assistant|Chatbot|Bot|AI|Réponse(?:\s+finale|\s+générée|\s+définitive|\s+justifiée)?)\s*(?:\*\*)?\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Strip residual special tokens
    text = re.sub(r"<\|[^>]+>", "", text)
    return text.strip()


# ── Helpers to call AI backend ────────────────────────────────────────────────

def _get_colab_config():
    """Return (url, key) or raise if not configured."""
    url = getattr(settings, "COLAB_API_URL", None)
    key = getattr(settings, "COLAB_API_KEY", None)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="COLAB_API_URL is not set in .env. Please configure your Colab server.",
        )
    return url, key


async def _call_colab(prompt: str) -> str:
    base_url, api_key = _get_colab_config()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    payload = {"prompt": prompt, "temperature": 0.4, "max_tokens": CHAT_MAX_TOKENS}

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(f"{base_url}/generate", json=payload, headers=headers)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Impossible de joindre le serveur Colab ({base_url}). "
                "Vérifie que le notebook est démarré et que l'URL ngrok est à jour dans le .env."
            ),
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le serveur Colab n'a pas répondu dans les 45 secondes. Réessaie.",
        )

    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Clé API Colab invalide (401 Unauthorized). "
                "Relance le notebook Colab et mets à jour COLAB_API_KEY dans le .env, puis redémarre le backend."
            ),
        )
    if resp.status_code == 502:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Le tunnel ngrok retourne 502 Bad Gateway. "
                "L'URL ngrok a peut-être changé. Relance le notebook et mets à jour COLAB_API_URL."
            ),
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur du serveur Colab : HTTP {resp.status_code} — {resp.text[:200]}",
        )

    return resp.json().get("generated_text", "").strip()


async def _call_ollama(prompt: str) -> str:
    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model    = getattr(settings, "OLLAMA_MODEL", "llama3.2")
    payload  = {"model": model, "prompt": prompt, "stream": False,
                 "options": {"temperature": 0.4, "num_predict": CHAT_MAX_TOKENS}}
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(f"{base_url}/api/generate", json=payload)
            resp.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama introuvable sur {base_url}. Lance `ollama serve` et réessaie.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama n'a pas répondu dans les 45 secondes.",
        )
    return resp.json().get("response", "").strip()


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(message: str, context: Optional[dict], history: list) -> str:
    lines = [
        "Tu es un assistant pédagogique bienveillant, précis et concis pour les étudiants.",
        "",
        "🚨 RÈGLES STRICTES :",
        "- Réponds DIRECTEMENT et naturellement à la question posée (3 à 5 phrases max).",
        "- N'AJOUTE AUCUN préfixe ou label (interdiction d'écrire 'Réponse :', 'Note :', 'Assistant :', etc.).",
        "- INTERDICTION ABSOLUE de simuler la suite du dialogue ou d'écrire une réplique d'étudiant.",
        "- ARRÊTE-TOI IMMÉDIATEMENT dès que ta réponse à la question est fournie.",
        "- Pas de bavardage superflu, sois encourageant et axé sur la réussite académique.",
    ]

    if context:
        ctx_parts = []
        if context.get("subjects"):
            ctx_parts.append(f"Matières : {', '.join(context['subjects'])}")
        if context.get("today_sessions"):
            sessions_str = "; ".join(
                f"{s['subject_name']} {s['start_time']}-{s['end_time']} "
                f"({'fait' if s.get('completed') else 'prévu'})"
                for s in context["today_sessions"]
            )
            ctx_parts.append(f"Aujourd'hui : {sessions_str}")
        if context.get("weekly_progress"):
            wp = context["weekly_progress"]
            ctx_parts.append(f"Progression : {wp.get('completed',0)}/{wp.get('total',0)} sessions")
        if ctx_parts:
            lines.append("\nContexte du planning de l'étudiant : " + " | ".join(ctx_parts))

    if history:
        lines.append("\nHistorique récent :")
        for msg in history[-4:]:
            role_label = "Étudiant" if msg.role == "user" else "Assistant"
            content = msg.content[:250] + "..." if len(msg.content) > 250 else msg.content
            clean_content = content.replace("\n", " ").strip()
            lines.append(f"[{role_label}] : {clean_content}")

    lines.append(f"\nQuestion actuelle de l'étudiant : {message.strip()}")
    lines.append("\nRéponse de l'assistant :")
    return "\n".join(lines)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str
    generation_time: float


# ── Health check ──────────────────────────────────────────────────────────────

@router.get("/health")
async def chat_health(current_user: User = Depends(get_current_user)):
    """
    Diagnostic connectivity check for the AI backend (Colab or Ollama).
    Returns a 200 JSON object with status details so frontend badges and
    indicators can display real-time status, latency, model, and GPU info.
    """
    use_colab = getattr(settings, "AI_SERVICE_TYPE", "ollama") == "colab"

    if use_colab:
        url = getattr(settings, "COLAB_API_URL", None)
        api_key = getattr(settings, "COLAB_API_KEY", None)

        if not url:
            return {
                "ok": False,
                "backend": "colab",
                "configured": False,
                "url": None,
                "latency_ms": None,
                "error": "COLAB_API_URL n'est pas configuré dans le fichier .env.",
            }

        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(f"{url}/health", headers=headers)
            latency_ms = round((time.time() - t0) * 1000)

            if resp.status_code == 401:
                return {
                    "ok": False,
                    "backend": "colab",
                    "configured": True,
                    "url": url,
                    "latency_ms": latency_ms,
                    "status_code": 401,
                    "error": "Clé API Colab invalide (401). Vérifiez COLAB_API_KEY dans le .env.",
                }

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    data = {}
                return {
                    "ok": True,
                    "backend": "colab",
                    "configured": True,
                    "url": url,
                    "latency_ms": latency_ms,
                    "status_code": 200,
                    "model": data.get("model", "Llama-3.1-8B-Instruct"),
                    "device": data.get("device"),
                    "gpu": data.get("gpu"),
                    "stats": data.get("stats"),
                }

            return {
                "ok": False,
                "backend": "colab",
                "configured": True,
                "url": url,
                "latency_ms": latency_ms,
                "status_code": resp.status_code,
                "error": f"Colab a retourné le code HTTP {resp.status_code}",
            }
        except httpx.ConnectError:
            return {
                "ok": False,
                "backend": "colab",
                "configured": True,
                "url": url,
                "latency_ms": None,
                "error": f"Serveur Colab inaccessible ({url}). Vérifiez que le notebook tourne et que ngrok est actif.",
            }
        except httpx.TimeoutException:
            return {
                "ok": False,
                "backend": "colab",
                "configured": True,
                "url": url,
                "latency_ms": None,
                "error": "Le serveur Colab ne répond pas (>8s). Il est peut-être en train de démarrer ou occupé.",
            }
        except Exception as e:
            return {
                "ok": False,
                "backend": "colab",
                "configured": True,
                "url": url,
                "latency_ms": None,
                "error": f"Erreur de connexion Colab : {str(e)}",
            }
    else:
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
            latency_ms = round((time.time() - t0) * 1000)
            models = resp.json().get("models", []) if resp.status_code == 200 else []
            model_names = [m.get("name") for m in models]
            return {
                "ok": True,
                "backend": "ollama",
                "configured": True,
                "url": base_url,
                "latency_ms": latency_ms,
                "status_code": resp.status_code,
                "model": getattr(settings, "OLLAMA_MODEL", "llama3.2"),
                "available_models": model_names,
            }
        except Exception as e:
            return {
                "ok": False,
                "backend": "ollama",
                "configured": True,
                "url": base_url,
                "latency_ms": None,
                "error": f"Ollama local inaccessible sur {base_url}. Lancez `ollama serve`.",
            }


# ── Main chat endpoint ────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI study assistant.
    Returns a short, focused reply (max 350 tokens).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message vide.")
    if len(request.message) > 1000:
        raise HTTPException(status_code=400, detail="Message trop long (max 1000 caractères).")

    use_colab = getattr(settings, "AI_SERVICE_TYPE", "ollama") == "colab"
    prompt = _build_prompt(
        message=request.message.strip(),
        context=request.context,
        history=request.history or [],
    )

    start = time.time()
    if use_colab:
        reply = await _call_colab(prompt)
    else:
        reply = await _call_ollama(prompt)

    reply = _truncate_hallucination(reply)
    if not reply:
        reply = "Désolé, je n'ai pas pu générer une réponse. Réessaie dans quelques instants."

    return ChatResponse(reply=reply, generation_time=round(time.time() - start, 2))
