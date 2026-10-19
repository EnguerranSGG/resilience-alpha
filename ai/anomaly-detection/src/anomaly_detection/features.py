"""Définition des features et de leur source PromQL.

Les expressions s'appuient sur les recording rules de
``infrastructure/prometheus/rules/features.yml`` (fenêtre glissante de 30 s).
"""

from __future__ import annotations

FEATURES: tuple[str, ...] = (
    "request_rate",
    "latency_p95",
    "error_rate",
    "cpu_usage",
    "active_requests",
)

PROMQL: dict[str, str] = {
    "request_rate": "resilience:request_rate:30s",
    "latency_p95": "resilience:latency_p95_ms:30s",
    "error_rate": "resilience:error_rate:30s",
    "cpu_usage": "resilience:cpu_usage:30s",
    "active_requests": "resilience:active_requests",
}

WINDOW_SECONDS = 30
LABEL_COLUMN = "label"  # 0 = normal, 1 = anomalie / attaque (données étiquetées uniquement)
SYNTHETIC_COLUMN = "is_synthetic"
