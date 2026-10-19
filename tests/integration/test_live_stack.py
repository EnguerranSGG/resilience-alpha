"""T01-T06 — tests d'acceptation sur la stack Docker démarrée.

Ils sont ignorés si `make up` n'a pas été lancé. Ils ne fabriquent pas de résultat :
l'absence de stack est un skip, pas un succès.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.live]

GATEWAY = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="module", autouse=True)
def _stack(require_live_stack: None) -> None:
    return None


def test_t01_postgres_is_healthy(compose_exec: Callable[..., str]) -> None:
    output = compose_exec("postgres", "pg_isready", "-U", "payments", "-d", "payments")
    assert "accepting connections" in output


def test_t02_payment_api_healthchecks() -> None:
    live = httpx.get(f"{GATEWAY}/api/health/live", timeout=5)
    ready = httpx.get(f"{GATEWAY}/api/health/ready", timeout=5)
    assert live.status_code == 200
    assert ready.status_code == 200
    body = ready.json()
    assert body["checks"]["database"] is True


def test_t03_and_t04_fictional_payment_and_idempotency(repo_root: Path) -> None:
    password_file = repo_root / "secrets" / "demo_password"
    if not password_file.is_file():
        pytest.skip("secrets/demo_password absent")
    password = password_file.read_text(encoding="utf-8")
    login = httpx.post(
        f"{GATEWAY}/auth/login",
        json={"username": "demo", "password": password},
        timeout=5,
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    key = f"t03-{uuid.uuid4().hex[:16]}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key,
        "Content-Type": "application/json",
    }
    payload = {"amount": "2.50", "currency": "EUR", "description": "t03-t04"}
    first = httpx.post(f"{GATEWAY}/api/payments", headers=headers, json=payload, timeout=10)
    second = httpx.post(f"{GATEWAY}/api/payments", headers=headers, json=payload, timeout=10)
    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert second.headers.get("Idempotent-Replayed") == "true"
    fetched = httpx.get(
        f"{GATEWAY}/api/payments/{first.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    assert fetched.status_code == 200
    assert fetched.json()["status"] in {"PENDING", "COMPLETED", "FAILED"}


def test_t05_prometheus_scrapes_payment_api(compose_exec: Callable[..., str]) -> None:
    raw = compose_exec(
        "prometheus",
        "wget",
        "-qO-",
        "http://127.0.0.1:9090/api/v1/query?query=up{job=%22payment-api%22}",
    )
    payload = json.loads(raw)
    assert payload["status"] == "success"
    results = payload["data"]["result"]
    assert results, "Prometheus n'a pas encore de série up{job=payment-api}"
    assert results[0]["value"][1] == "1"


def test_t06_loki_is_ready_and_can_receive_logs(compose_exec: Callable[..., str]) -> None:
    # /ready peut répondre 503 sur une instance unique (anneau ingester) alors que
    # Loki scrape et ingère déjà : on s'appuie sur Prometheus + l'API labels.
    up = json.loads(
        compose_exec(
            "prometheus",
            "wget",
            "-qO-",
            "http://127.0.0.1:9090/api/v1/query?query=up{job=%22loki%22}",
        )
    )
    assert up["data"]["result"][0]["value"][1] == "1"
    httpx.get(f"{GATEWAY}/api/health/live", timeout=5)
    labels = json.loads(compose_exec("prometheus", "wget", "-qO-", "http://loki:3100/loki/api/v1/labels"))
    assert labels["status"] == "success"
    assert "service" in labels["data"]
    ingested = json.loads(
        compose_exec(
            "prometheus",
            "wget",
            "-qO-",
            "http://127.0.0.1:9090/api/v1/query?query=loki_distributor_bytes_received_total",
        )
    )
    total = sum(float(row["value"][1]) for row in ingested["data"]["result"])
    assert total > 0, "Loki n'a reçu aucun octet"
