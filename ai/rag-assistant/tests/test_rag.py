"""T12 (partie unitaire) — l'assistant démarre et répond sans le socle métier ni Ollama.

Embeddings et LLM factices : on teste l'indexation, la recherche et la citation
des sources, pas la qualité des réponses du modèle réel.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from rag_assistant.api import create_app
from rag_assistant.config import Settings
from rag_assistant.index import build_index, load_index
from rag_assistant.loader import load_documents
from rag_assistant.qa import answer

DOCUMENTS = Path(__file__).resolve().parents[1] / "documents"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(document_dirs=[DOCUMENTS], index_path=tmp_path / "index.json", ollama_url="http://127.0.0.1:9")


@pytest.fixture
def embeddings() -> DeterministicFakeEmbedding:
    return DeterministicFakeEmbedding(size=64)


def test_initial_documents_are_present() -> None:
    names = {p.name for p in DOCUMENTS.glob("*.md")}
    assert {"procedure-incident.md", "architecture.md", "procedure-reprise.md", "composants.md"} <= names


def test_documents_are_chunked_with_sources(settings: Settings) -> None:
    chunks = load_documents(settings.document_dirs, settings.chunk_size, settings.chunk_overlap)
    assert len(chunks) > 4
    assert all(c.metadata["source"].startswith("documents/") for c in chunks)


def test_index_is_persisted_and_reloaded(settings: Settings, embeddings) -> None:
    _, count = build_index(settings, embeddings)
    reloaded = load_index(settings.index_path, embeddings)
    assert reloaded is not None and count > 0
    assert len(reloaded.similarity_search("WAF", k=2)) == 2


def test_answer_cites_sources(settings: Settings, embeddings) -> None:
    store, _ = build_index(settings, embeddings)
    llm = FakeListChatModel(responses=["Le WAF filtre les requêtes [1]."])
    result = answer("Quel est le rôle du WAF ?", store, llm, k=3)
    assert result.answer.startswith("Le WAF")
    assert [s.ref for s in result.sources] == [1, 2, 3]


def test_api_starts_without_ollama_and_reports_degraded(settings: Settings, embeddings) -> None:
    app = create_app(settings, embeddings, FakeListChatModel(responses=["ok"]))
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json()["checks"] == {"index": False, "ollama": False}
        assert client.post("/ask", json={"question": "Quel est le rôle du WAF ?"}).status_code == 503


def test_api_answers_with_index(settings: Settings, embeddings) -> None:
    build_index(settings, embeddings)
    app = create_app(settings, embeddings, FakeListChatModel(responses=["Réponse [1]"]))
    with TestClient(app) as client:
        body = client.post("/ask", json={"question": "Étapes de reprise ?"}).json()
        page = client.post("/", data={"question": "<script>alert(1)</script>"}).text
    assert body["answer"] == "Réponse [1]" and body["sources"]
    assert "<script>alert(1)</script>" not in page
