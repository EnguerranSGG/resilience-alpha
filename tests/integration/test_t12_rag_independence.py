"""T12 — l'assistant RAG peut démarrer indépendamment du socle métier."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration


def test_t12_rag_profile_does_not_depend_on_business_services(repo_root: Path) -> None:
    compose = yaml.safe_load((repo_root / "infrastructure" / "docker" / "compose.yml").read_text(encoding="utf-8"))
    rag = compose["services"]["rag-assistant"]
    ollama = compose["services"]["ollama"]
    assert rag.get("profiles") == ["rag"]
    assert ollama.get("profiles") == ["rag"]
    depends = rag.get("depends_on") or {}
    names = set(depends)
    assert names <= {"ollama"}
    assert "payment-api" not in names
    assert "postgres" not in names
    assert "remediation" not in names


def test_t12_core_compose_does_not_start_ollama_by_default(repo_root: Path) -> None:
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    assert "up: .env ## Démarre le socle (sans RAG)" in makefile
    assert "--profile rag" in makefile


def test_t12_unit_coverage_exists(repo_root: Path) -> None:
    tests = (repo_root / "ai" / "rag-assistant" / "tests" / "test_rag.py").read_text(encoding="utf-8")
    assert "test_api_starts_without_ollama_and_reports_degraded" in tests
    assert "test_initial_documents_are_present" in tests
