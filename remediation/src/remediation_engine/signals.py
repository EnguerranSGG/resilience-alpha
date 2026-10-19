"""Signaux de corroboration indépendants du détecteur ML.

Le moteur ne se fie pas aux métriques recopiées dans l'événement ML : il
interroge lui-même Prometheus (dégradation du service) et Loki (événements de
sécurité de la passerelle).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

LATENCY_QUERY = "resilience:latency_p95_ms:30s"
ERROR_RATE_QUERY = "resilience:error_rate:30s"
SECURITY_QUERY = 'sum(count_over_time({service="gateway", log_type="access"} | json | status =~ "429|403" [1m]))'


@dataclass(frozen=True)
class DegradationReport:
    available: bool
    latency_p95_ms: float | None = None
    error_rate: float | None = None


@dataclass(frozen=True)
class SecurityReport:
    available: bool
    blocked_requests_1m: int | None = None


class DegradationProbe(Protocol):
    def measure(self) -> DegradationReport: ...


class SecuritySignalSource(Protocol):
    def measure(self) -> SecurityReport: ...


def _first_value(payload: dict) -> float | None:
    results = payload.get("data", {}).get("result", [])
    if not results:
        return None
    value = float(results[0]["value"][1])
    return None if value != value else value  # NaN → None


class PrometheusDegradationProbe:
    def __init__(self, base_url: str, timeout: float, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def _query(self, expr: str) -> float | None:
        response = self._client.get("/api/v1/query", params={"query": expr})
        response.raise_for_status()
        return _first_value(response.json())

    def measure(self) -> DegradationReport:
        try:
            return DegradationReport(
                available=True,
                latency_p95_ms=self._query(LATENCY_QUERY),
                error_rate=self._query(ERROR_RATE_QUERY),
            )
        except (httpx.HTTPError, KeyError, ValueError):
            logger.warning("signals.prometheus_unavailable", exc_info=True)
            return DegradationReport(available=False)


class LokiSecuritySignals:
    def __init__(self, base_url: str, timeout: float, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def measure(self) -> SecurityReport:
        try:
            response = self._client.get("/loki/api/v1/query", params={"query": SECURITY_QUERY})
            response.raise_for_status()
            value = _first_value(response.json())
            return SecurityReport(available=True, blocked_requests_1m=int(value or 0))
        except (httpx.HTTPError, KeyError, ValueError):
            logger.warning("signals.loki_unavailable", exc_info=True)
            return SecurityReport(available=False)


class StaticDegradationProbe:
    """Implémentation de test : renvoie une mesure fixée."""

    def __init__(self, report: DegradationReport) -> None:
        self.report = report

    def measure(self) -> DegradationReport:
        return self.report


class StaticSecuritySignals:
    def __init__(self, report: SecurityReport) -> None:
        self.report = report

    def measure(self) -> SecurityReport:
        return self.report
