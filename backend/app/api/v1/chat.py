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

# Patterns that mean the model started hallucinating a new turn
_STOP_RE = re.compile(
    r"\n---|\n###\s+(QUESTION|HISTORIQUE|FIN|NOTE|MESSAGE|CONTEXTE|PROGRESSION|EMPLOI)|"
    r"\n(Étudiant|Student|User)\s*:|\n(Assistant|Chatbot|Bot)\s*:|"
    r"### FIN|\[FIN\]|fin de (la|le) session|note de l.assistant",
    re.IGNORECASE,
)


def _truncate_hallucination(text: str) -> str:
    m = _STOP_RE.search(text)
    return text[: m.start()].rstrip() if m else text


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
        "Tu es un assistant pédagogique intégré dans une app de planning d'études.",
        "Réponds de façon COURTE et DIRECTE (3-6 phrases max).",
        "Ne génère PAS de note finale, de séparateur ---, ni d'historique.",
        "Réponds dans la langue de l'étudiant.",
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
            lines.append("\nContexte planning : " + " | ".join(ctx_parts))

    if history:
        lines.append("")
        for msg in history[-4:]:
            label = "Étudiant" if msg.role == "user" else "Toi"
            content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
            lines.append(f"{label} : {content}")

    lines.append(f"\nÉtudiant : {message}")
    lines.append("Toi :")
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
    Quick connectivity check for the AI backend.
    Returns { ok: true, backend: "colab"|"ollama", url: "..." }
    or raises 503 with a descriptive error.
    """
    use_colab = getattr(settings, "AI_SERVICE_TYPE", "ollama") == "colab"

    if use_colab:
        base_url, api_key = _get_colab_config()
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(f"{base_url}/health", headers=headers)
            if resp.status_code == 401:
                raise HTTPException(status_code=503,
                    detail="Clé API Colab invalide (401). Mets à jour COLAB_API_KEY dans .env.")
            return {"ok": True, "backend": "colab", "url": base_url, "status": resp.status_code}
        except httpx.ConnectError:
            raise HTTPException(status_code=503,
                detail=f"Serveur Colab inaccessible ({base_url}). Vérifie le notebook et l'URL ngrok.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=503,
                detail="Serveur Colab trop lent à répondre (>8s). Il est peut-être en train de démarrer.")
    else:
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
            return {"ok": True, "backend": "ollama", "url": base_url}
        except Exception:
            raise HTTPException(status_code=503,
                detail=f"Ollama inaccessible sur {base_url}. Lance `ollama serve`.")


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
