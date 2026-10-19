"""Couverture statique des tests d'acceptation T07, T08, T09 (exécutés aussi en unitaire)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from resilience_contracts import AnomalyEvent, RecommendedAction

pytestmark = pytest.mark.integration


def test_t07_training_roundtrip_is_covered(repo_root: Path) -> None:
    pipeline = (repo_root / "ai" / "anomaly-detection" / "tests" / "test_pipeline.py").read_text(encoding="utf-8")
    assert "test_train_save_and_load_roundtrip" in pipeline
    assert "trained_on_synthetic" in pipeline


def test_t08_example_event_matches_schema(repo_root: Path) -> None:
    example = (repo_root / "docs" / "contracts" / "examples" / "anomaly-event.v1.json").read_text(encoding="utf-8")
    event = AnomalyEvent.model_validate_json(example)
    assert event.type.value == "DOS_SUSPECTED"
    assert event.recommended_action is RecommendedAction.ENABLE_RATE_LIMIT
    assert event.trained_on_synthetic is True


def test_t08_malformed_event_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate({"event_id": "x", "recommended_action": "rm -rf /"})


def test_t09_unauthorized_action_is_covered(repo_root: Path) -> None:
    engine_tests = (repo_root / "remediation" / "tests" / "test_engine.py").read_text(encoding="utf-8")
    assert "test_unauthorized_recommended_action_is_rejected" in engine_tests
    assert "test_unconfirmed_anomaly_does_not_remediate" in engine_tests
    assert "test_failed_playbook_leads_to_failed_state" in engine_tests
