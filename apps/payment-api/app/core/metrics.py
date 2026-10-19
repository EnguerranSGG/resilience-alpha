"""Métriques Prometheus exposées sur ``/metrics``.

Les noms sont repris par les recording rules Prometheus et par le détecteur ML
(``infrastructure/prometheus/rules/features.yml``) : ne pas les renommer sans
mettre à jour ces deux consommateurs.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "Requêtes HTTP traitées.", ["method", "route", "status"])
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Durée de traitement des requêtes HTTP.",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
HTTP_IN_PROGRESS = Gauge("http_requests_in_progress", "Requêtes HTTP en cours.", ["method"])
PAYMENTS_PROCESSED = Counter("payments_processed_total", "Paiements fictifs traités.", ["status"])
PAYMENTS_REPLAYED = Counter("payments_idempotent_replays_total", "Requêtes rejouées avec une clé d'idempotence connue.")
DATABASE_UP = Gauge("payment_database_up", "1 si la base répond au dernier contrôle de disponibilité.")


def _route_template(request: Request) -> str:
    # Gabarit de route (ex. "/payments/{payment_id}") renseigné par le routeur :
    # borne la cardinalité même si un client envoie des chemins aléatoires.
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"


def install_http_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def _http_metrics(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)
        method = request.method
        HTTP_IN_PROGRESS.labels(method).inc()
        start = time.perf_counter()
        status = "500"
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        finally:
            route = _route_template(request)
            HTTP_IN_PROGRESS.labels(method).dec()
            HTTP_LATENCY.labels(method, route).observe(time.perf_counter() - start)
            HTTP_REQUESTS.labels(method, route, status).inc()
