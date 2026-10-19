"""T09 et contrat de l'API interne du moteur."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from remediation_engine.main import create_app

from .conftest import TOKEN

EXAMPLE = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "examples" / "anomaly-event.v1.json"


@pytest.fixture
def client(settings, make_engine):
    app = create_app(settings=settings, engine=make_engine(), run_ticker=False)
    with TestClient(app) as c:
        yield c


def _event(**overrides):
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    payload["trained_on_synthetic"] = False
    payload.update(overrides)
    return payload


def test_valid_event_is_accepted(client: TestClient) -> None:
    response = client.post("/events", json=_event(), headers={"X-Resilience-Token": TOKEN})
    assert response.status_code == 202
    assert response.json()["outcome"] == "MITIGATE"
    assert client.get("/public/status").json()["state"] == "RECOVERED"
    incidents = client.get("/public/incidents").json()
    assert incidents[0]["execution_mode"] == "simulated"


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "DOS_SUSPECTED"},
        _event(anomaly_score="very low"),
        _event(recommended_action="bash -c 'reboot'"),
        _event(playbook="/etc/shadow"),
    ],
)
def test_malformed_event_is_rejected(client: TestClient, payload: dict) -> None:
    response = client.post("/events", json=payload, headers={"X-Resilience-Token": TOKEN})
    assert response.status_code == 422
    assert client.get("/status").json()["state"] == "NORMAL"


def test_unauthorized_action_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/events", json=_event(recommended_action="RESTART_SERVICE"), headers={"X-Resilience-Token": TOKEN}
    )
    assert response.status_code == 202
    assert response.json()["outcome"] == "REJECT"


def test_missing_or_wrong_token_is_refused(client: TestClient) -> None:
    assert client.post("/events", json=_event()).status_code == 401
    assert client.post("/events", json=_event(), headers={"X-Resilience-Token": "nope"}).status_code == 401


def test_no_token_configured_refuses_all_events(make_engine) -> None:
    from remediation_engine.config import Settings

    app = create_app(settings=Settings(), engine=make_engine(), run_ticker=False)
    with TestClient(app) as c:
        assert c.post("/events", json=_event(), headers={"X-Resilience-Token": "x"}).status_code == 503
        assert c.get("/health/ready").status_code == 503


def test_no_route_executes_arbitrary_commands(client: TestClient) -> None:
    paths = {route.path for route in client.app.routes}
    assert not any(word in p for p in paths for word in ("exec", "command", "shell", "playbook"))


def test_metrics_expose_state_and_simulation_flag(client: TestClient) -> None:
    body = client.get("/metrics").text
    assert 'remediation_state{state="NORMAL"} 1.0' in body
    assert "remediation_executor_simulated 1.0" in body
