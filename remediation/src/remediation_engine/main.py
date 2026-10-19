"""API interne du moteur de remédiation.

* ``POST /events`` : réception des événements ML (jeton partagé obligatoire,
  réseau d'observabilité uniquement).
* ``GET /public/status`` et ``GET /public/incidents`` : vues en lecture seule,
  seules routes relayées par la passerelle pour le dashboard.

Aucune route ne permet d'exécuter une commande ou de choisir un playbook.
"""

from __future__ import annotations

import hmac
import json
import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from remediation_engine.config import PolicySettings, Settings
from remediation_engine.engine import RemediationEngine
from remediation_engine.executor import (
    PROFILE_AFTER_ACTION,
    ActionExecutor,
    AnsibleExecutor,
    SimulatedExecutor,
)
from remediation_engine.incidents import IncidentStore
from remediation_engine.logging_setup import configure_logging
from remediation_engine.signals import LokiSecuritySignals, PrometheusDegradationProbe
from remediation_engine.verification import BusinessVerifier
from resilience_contracts import AnomalyEvent, ExecutionMode, IncidentView, RemediationStatusView

logger = logging.getLogger(__name__)
GATEWAY_PROFILES = frozenset(PROFILE_AFTER_ACTION.values())


class EventAck(BaseModel):
    outcome: str
    reasons: list[str]
    state: str


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    checks: dict[str, bool] = {}


def build_executor(settings: Settings) -> ActionExecutor:
    if settings.execution_mode is ExecutionMode.ANSIBLE:
        return AnsibleExecutor(
            settings.ansible_playbook_dir,
            settings.ansible_inventory,
            settings.ansible_timeout_seconds,
            settings.ansible_playbook_bin,
        )
    return SimulatedExecutor()


def read_gateway_profile(path: Path | None) -> str | None:
    """Profil confirmé par le dernier accusé de la passerelle (``status.json``), sinon None."""
    if path is None or not path.is_file():
        return None
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(status, dict) or status.get("result") != "applied":
        return None
    profile = status.get("profile")
    return profile if profile in GATEWAY_PROFILES else None


def build_engine(settings: Settings) -> RemediationEngine:
    engine = RemediationEngine(
        settings=settings,
        policy=PolicySettings(),
        executor=build_executor(settings),
        verifier=BusinessVerifier(
            settings.gateway_url,
            settings.probe_username,
            settings.probe_password_value,
            settings.http_timeout_seconds,
            settings.verification_attempts,
            settings.verification_delay_seconds,
        ),
        degradation=PrometheusDegradationProbe(settings.prometheus_url, settings.http_timeout_seconds),
        security=LokiSecuritySignals(settings.loki_url, settings.http_timeout_seconds),
        store=IncidentStore(settings.journal_file),
    )
    if settings.execution_mode is ExecutionMode.ANSIBLE:
        engine.adopt_observed_profile(read_gateway_profile(settings.gateway_status_file))
    return engine


def create_app(
    settings: Settings | None = None,
    engine: RemediationEngine | None = None,
    run_ticker: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level, settings.log_file)
    engine = engine or build_engine(settings)
    stop = threading.Event()

    def ticker() -> None:
        while not stop.wait(settings.tick_interval_seconds):
            try:
                engine.tick()
            except Exception:
                logger.exception("remediation.tick_failed")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        thread = threading.Thread(target=ticker, name="remediation-ticker", daemon=True)
        if run_ticker:
            thread.start()
        if engine.executor.mode is ExecutionMode.SIMULATED:
            logger.warning(
                "startup.simulated_executor",
                extra={"event": "startup.simulated_executor", "note": "aucune action réelle"},
            )
        yield
        stop.set()

    app = FastAPI(title="RESILIENCE-ALPHA remediation-engine", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine

    @app.post("/events", response_model=EventAck, status_code=status.HTTP_202_ACCEPTED)
    def receive_event(
        event: AnomalyEvent,
        request: Request,
        token: Annotated[str | None, Header(alias="X-Resilience-Token")] = None,
    ) -> EventAck:
        expected = settings.event_token_value
        if not expected:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Jeton d'ingestion non configuré")
        if not token or not hmac.compare_digest(token.encode(), expected.encode()):
            client = request.client.host if request.client else "unknown"
            logger.warning("events.unauthorized", extra={"event": "events.unauthorized", "client": client})
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Jeton invalide")
        decision = engine.handle_event(event)
        return EventAck(outcome=decision.outcome.value, reasons=decision.reasons, state=engine.state.value)

    @app.get("/status", response_model=RemediationStatusView)
    @app.get("/public/status", response_model=RemediationStatusView)
    def get_status() -> RemediationStatusView:
        return engine.status()

    @app.get("/incidents", response_model=list[IncidentView])
    @app.get("/public/incidents", response_model=list[IncidentView])
    def get_incidents() -> list[IncidentView]:
        return [incident.view() for incident in engine.store.recent()]

    @app.get("/health/live", response_model=Health)
    def live() -> Health:
        return Health(status="ok", service=settings.service_name)

    @app.get("/health/ready", response_model=Health)
    def ready(response: Response) -> Health:
        checks = {
            "event_token": bool(settings.event_token_value),
            "probe_credentials": bool(settings.probe_password_value),
        }
        if settings.execution_mode is ExecutionMode.ANSIBLE:
            checks["playbooks"] = (settings.ansible_playbook_dir / "mitigate.yml").is_file()
        healthy = all(checks.values())
        if not healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return Health(status="ok" if healthy else "degraded", service=settings.service_name, checks=checks)

    @app.get("/metrics", include_in_schema=False)
    def get_metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
