"""T08 — un événement ML respecte son schéma (tests de contrat)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from resilience_contracts import AnomalyEvent, RecommendedAction
from resilience_contracts.export_schemas import SCHEMAS, render

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPO_ROOT / "docs" / "contracts"


def _valid_payload() -> dict:
    return json.loads((CONTRACTS_DIR / "examples" / "anomaly-event.v1.json").read_text(encoding="utf-8"))


def test_published_example_is_valid() -> None:
    event = AnomalyEvent.model_validate(_valid_payload())
    assert event.recommended_action is RecommendedAction.ENABLE_RATE_LIMIT


def test_unknown_field_is_rejected() -> None:
    payload = _valid_payload() | {"command": "rm -rf /"}
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate(payload)


def test_free_text_action_is_rejected() -> None:
    payload = _valid_payload() | {"recommended_action": "docker restart payment-api"}
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate(payload)


def test_unsupported_schema_version_is_rejected() -> None:
    payload = _valid_payload() | {"schema_version": "2.0"}
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate(payload)


def test_naive_timestamp_is_rejected() -> None:
    payload = _valid_payload() | {"timestamp": "2026-10-19T10:30:00"}
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate(payload)


def test_event_id_pattern_blocks_injection() -> None:
    payload = _valid_payload() | {"event_id": "abc; curl evil"}
    with pytest.raises(ValidationError):
        AnomalyEvent.model_validate(payload)


@pytest.mark.parametrize("filename", sorted(SCHEMAS))
def test_published_json_schemas_are_up_to_date(filename: str) -> None:
    published = (CONTRACTS_DIR / filename).read_text(encoding="utf-8")
    assert published == render(SCHEMAS[filename]), "Schéma JSON obsolète : lancer `make contracts`"
