"""Inférence et construction de l'événement d'anomalie (contrat v1)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta

from anomaly_detection.features import WINDOW_SECONDS
from anomaly_detection.model import ModelBundle
from anomaly_detection.preprocess import vectorize
from resilience_contracts import (
    SCHEMA_VERSION,
    AnomalyEvent,
    AnomalyType,
    DetectionWindow,
    MetricsSnapshot,
    RecommendedAction,
)


@dataclass(frozen=True)
class Prediction:
    score: float
    is_anomaly: bool


def score(bundle: ModelBundle, observation: Mapping[str, float]) -> Prediction:
    frame = vectorize(observation)
    value = float(bundle.scores(frame).iloc[0])
    return Prediction(score=max(-1.0, min(1.0, value)), is_anomaly=value < bundle.metadata.threshold)


def qualify(bundle: ModelBundle, observation: Mapping[str, float]) -> AnomalyType:
    """Qualification heuristique du type : le trafic dépasse-t-il nettement le p99 appris ?

    Ce n'est pas une preuve d'attaque ; le moteur de remédiation corrobore.
    """
    p99 = bundle.metadata.training_quantiles.get("request_rate", {}).get("p99", 0.0)
    rate = observation.get("request_rate") or 0.0
    return AnomalyType.DOS_SUSPECTED if rate > max(3 * p99, 10.0) else AnomalyType.ANOMALY_DETECTED


def build_event(
    bundle: ModelBundle,
    observation: Mapping[str, float],
    prediction: Prediction,
    consecutive: int,
    now: datetime,
    source: str = "ml-detector",
) -> AnomalyEvent:
    anomaly_type = qualify(bundle, observation)

    def clean(name: str) -> float | None:
        value = observation.get(name)
        return None if value is None or value != value else max(float(value), 0.0)

    error_rate = clean("error_rate")
    return AnomalyEvent(
        schema_version=SCHEMA_VERSION,
        event_id=f"evt-{uuid.uuid4().hex[:16]}",
        type=anomaly_type,
        timestamp=now,
        source=source,
        model="isolation_forest",
        model_version=bundle.metadata.model_version,
        trained_on_synthetic=bundle.metadata.trained_on_synthetic,
        anomaly_score=prediction.score,
        threshold=bundle.metadata.threshold,
        is_anomaly=prediction.is_anomaly,
        window=DetectionWindow(
            start=now - timedelta(seconds=WINDOW_SECONDS),
            end=now,
            consecutive_anomalous_windows=consecutive,
        ),
        metrics=MetricsSnapshot(
            request_rate=clean("request_rate"),
            latency_p95_ms=clean("latency_p95"),
            error_rate=min(error_rate, 1.0) if error_rate is not None else None,
            cpu_usage=clean("cpu_usage"),
            active_requests=clean("active_requests"),
        ),
        recommended_action=(
            RecommendedAction.ENABLE_RATE_LIMIT if anomaly_type is AnomalyType.DOS_SUSPECTED else RecommendedAction.NONE
        ),
    )
