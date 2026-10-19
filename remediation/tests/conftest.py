from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from remediation_engine.config import PolicySettings, Settings
from remediation_engine.engine import RemediationEngine
from remediation_engine.executor import SimulatedExecutor
from remediation_engine.incidents import IncidentStore
from remediation_engine.signals import (
    DegradationReport,
    SecurityReport,
    StaticDegradationProbe,
    StaticSecuritySignals,
)
from remediation_engine.verification import BusinessVerifier
from resilience_contracts import AnomalyEvent

TOKEN = "test-token-not-a-secret"


class FakeGateway:
    """Simule la passerelle publique pour la vérification métier."""

    def __init__(self) -> None:
        self.ready_status = 200
        self.payment_status = "COMPLETED"
        self.duplicate_on_replay = False
        self.payments: dict[str, dict[str, Any]] = {}
        self.calls: list[str] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(f"{request.method} {request.url.path}")
        path = request.url.path
        if path == "/api/health/ready":
            return httpx.Response(self.ready_status, json={"status": "ok"})
        if path == "/auth/login":
            return httpx.Response(200, json={"access_token": "t", "token_type": "bearer", "expires_in": 60})
        if path == "/api/payments" and request.method == "POST":
            key = request.headers["Idempotency-Key"]
            if key in self.payments and not self.duplicate_on_replay:
                return httpx.Response(200, json=self.payments[key])
            payment = {"id": str(uuid.uuid4()), "status": self.payment_status, **json.loads(request.content)}
            self.payments[key] = payment
            return httpx.Response(201, json=payment)
        if path.startswith("/api/payments/"):
            return httpx.Response(200, json={"id": path.rsplit("/", 1)[-1]})
        return httpx.Response(404)


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        event_token=TOKEN,
        probe_password="probe-test-password",
        verification_attempts=2,
        verification_delay_seconds=0,
        suspect_timeout_seconds=60,
        restore_after_seconds=120,
        retry_cooldown_seconds=10,
        max_attempts=2,
    )


@pytest.fixture
def policy() -> PolicySettings:
    return PolicySettings(accept_synthetic_model=False, min_consecutive_windows=3)


@pytest.fixture
def degraded() -> StaticDegradationProbe:
    return StaticDegradationProbe(DegradationReport(True, latency_p95_ms=1500, error_rate=0.2))


@pytest.fixture
def security() -> StaticSecuritySignals:
    return StaticSecuritySignals(SecurityReport(True, blocked_requests_1m=0))


@pytest.fixture
def executor() -> SimulatedExecutor:
    return SimulatedExecutor()


@pytest.fixture
def make_engine(
    settings: Settings,
    policy: PolicySettings,
    executor: SimulatedExecutor,
    degraded: StaticDegradationProbe,
    security: StaticSecuritySignals,
    gateway: FakeGateway,
    clock: Clock,
) -> Callable[..., RemediationEngine]:
    def _make(**overrides: Any) -> RemediationEngine:
        params: dict[str, Any] = {
            "settings": settings,
            "policy": policy,
            "executor": executor,
            "verifier": BusinessVerifier(
                "http://gateway.test",
                settings.probe_username,
                settings.probe_password_value,
                1.0,
                settings.verification_attempts,
                0,
                transport=httpx.MockTransport(gateway.handler),
            ),
            "degradation": degraded,
            "security": security,
            "store": IncidentStore(),
            "synchronous": True,
            "clock": clock,
        }
        params.update(overrides)
        return RemediationEngine(**params)

    return _make


@pytest.fixture
def make_event() -> Callable[..., AnomalyEvent]:
    def _make(**overrides: Any) -> AnomalyEvent:
        now = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "type": "DOS_SUSPECTED",
            "timestamp": now.isoformat(),
            "source": "ml-detector",
            "model": "isolation_forest",
            "model_version": "test",
            "trained_on_synthetic": False,
            "anomaly_score": -0.2,
            "threshold": 0.0,
            "is_anomaly": True,
            "window": {
                "start": (now - timedelta(seconds=30)).isoformat(),
                "end": now.isoformat(),
                "consecutive_anomalous_windows": 3,
            },
            "metrics": {"request_rate": 90, "latency_p95_ms": 1400, "error_rate": 0.18},
            "recommended_action": "ENABLE_RATE_LIMIT",
        }
        payload.update(overrides)
        return AnomalyEvent.model_validate(payload)

    return _make
