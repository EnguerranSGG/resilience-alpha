"""Reprise du profil réellement appliqué par la passerelle au démarrage du moteur."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from remediation_engine.main import read_gateway_profile
from resilience_contracts import RemediationState


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"profile": "mitigation", "result": "applied"}, "mitigation"),
        ({"profile": "normal", "result": "applied"}, "normal"),
        ({"profile": "mitigation", "result": "rejected"}, None),
        ({"profile": "../../etc/passwd", "result": "applied"}, None),
        (["not", "a", "dict"], None),
    ],
)
def test_read_gateway_profile(tmp_path: Path, payload: object, expected: str | None) -> None:
    assert read_gateway_profile(_write(tmp_path / "status.json", payload)) == expected


def test_read_gateway_profile_missing_or_corrupt(tmp_path: Path) -> None:
    assert read_gateway_profile(None) is None
    assert read_gateway_profile(tmp_path / "absent.json") is None
    corrupt = tmp_path / "status.json"
    corrupt.write_text("{", encoding="utf-8")
    assert read_gateway_profile(corrupt) is None


def test_adopted_profile_is_reported_without_action(make_engine, gateway) -> None:
    engine = make_engine()
    engine.adopt_observed_profile("mitigation")
    assert engine.status().active_profile == "mitigation"
    assert engine.state is RemediationState.NORMAL
    assert gateway.calls == []
