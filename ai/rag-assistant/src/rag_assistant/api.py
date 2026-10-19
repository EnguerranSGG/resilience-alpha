"""Interface web minimale (lecture seule) de l'assistant RAG."""

from __future__ import annotations

import html
from typing import Literal

import httpx
from fastapi import FastAPI, Form, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from rag_assistant.config import Settings
from rag_assistant.index import load_index
from rag_assistant.qa import Answer, answer

EXAMPLES = [
    "Comment fonctionne le moteur de remédiation ?",
    "Quelles sont les étapes de reprise après une surcharge HTTP ?",
    "Quel est le rôle du WAF ?",
    "Quels sont les risques résiduels du projet ?",
]


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, bool]


def create_app(
    settings: Settings | None = None,
    embeddings: Embeddings | None = None,
    llm: BaseChatModel | None = None,
) -> FastAPI:
    settings = settings or Settings()
    if embeddings is None or llm is None:
        from langchain_ollama import ChatOllama, OllamaEmbeddings

        embeddings = embeddings or OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_url)
        llm = llm or ChatOllama(
            model=settings.chat_model, base_url=settings.ollama_url, temperature=settings.temperature
        )

    app = FastAPI(title="RESILIENCE-ALPHA rag-assistant", version="0.1.0")
    state: dict[str, object] = {"store": None}

    def store():
        if state["store"] is None:
            state["store"] = load_index(settings.index_path, embeddings)
        return state["store"]

    def ask(question: str) -> Answer:
        current = store()
        if current is None:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Index absent : lancer `python -m rag_assistant.index`",
            )
        try:
            return answer(question, current, llm, settings.top_k)
        except (httpx.HTTPError, ConnectionError) as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Ollama injoignable") from exc

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", response_model=Health)
    def ready(response: Response) -> Health:
        checks = {"index": settings.index_path.is_file()}
        try:
            checks["ollama"] = httpx.get(f"{settings.ollama_url}/api/tags", timeout=2).status_code == 200
        except httpx.HTTPError:
            checks["ollama"] = False
        healthy = all(checks.values())
        if not healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return Health(status="ok" if healthy else "degraded", checks=checks)

    @app.post("/ask")
    def ask_json(payload: Question) -> Answer:
        return ask(payload.question)

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return _page()

    @app.post("/", response_class=HTMLResponse)
    def ask_form(question: str = Form(min_length=3, max_length=500)) -> str:
        try:
            result = ask(question)
        except HTTPException as exc:
            return _page(question, f"<p class='err'>{html.escape(str(exc.detail))}</p>")
        sources = "".join(
            f"<li>[{s.ref}] {html.escape(s.source)} — {html.escape(s.section)}</li>" for s in result.sources
        )
        body = f"<div class='answer'>{html.escape(result.answer)}</div><h3>Sources</h3><ol>{sources}</ol>"
        return _page(question, body)

    return app


def _page(question: str = "", body: str = "") -> str:
    examples = "".join(f"<option value='{html.escape(q)}'>" for q in EXAMPLES)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Assistant RESILIENCE-ALPHA</title>
<style>body{{font-family:system-ui;max-width:52rem;margin:2rem auto;padding:0 1rem}}
input{{width:100%;padding:.6rem}}.answer{{white-space:pre-wrap;background:#f4f4f5;padding:1rem;border-radius:.5rem}}
.err{{color:#b91c1c}}small{{color:#71717a}}</style></head><body>
<h1>Assistant documentaire</h1>
<small>Réponses générées localement à partir de la documentation du projet. Aucune action n'est exécutée.</small>
<form method="post"><input name="question" list="ex" value="{html.escape(question)}"
 placeholder="Posez une question…" required minlength="3" maxlength="500"><datalist id="ex">{examples}</datalist>
<button>Demander</button></form>{body}</body></html>"""
