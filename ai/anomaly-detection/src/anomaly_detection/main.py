"""Boucle de détection en ligne.

Toutes les ``DETECTOR_INTERVAL_SECONDS`` : collecte Prometheus → score →
compteur de fenêtres anormales consécutives → envoi d'un événement au moteur.

Sans modèle chargé, **aucun événement n'est émis** ; l'état est visible via
``ml_detector_model_loaded`` et dans les logs.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from prometheus_client import Counter, Gauge, start_http_server
from pydantic_settings import BaseSettings, SettingsConfigDict

from anomaly_detection.collect import CollectError, PrometheusCollector
from anomaly_detection.features import FEATURES
from anomaly_detection.model import ModelBundle, load
from anomaly_detection.predict import build_event, score

logger = logging.getLogger("anomaly_detection")

MODEL_LOADED = Gauge("ml_detector_model_loaded", "1 si un modèle est chargé.")
MODEL_SYNTHETIC = Gauge("ml_detector_model_synthetic", "1 si le modèle chargé est synthétique.")
ANOMALY_SCORE = Gauge("ml_detector_anomaly_score", "Dernier score Isolation Forest.")
IS_ANOMALY = Gauge("ml_detector_is_anomaly", "1 si la dernière fenêtre est anormale.")
CONSECUTIVE = Gauge("ml_detector_consecutive_anomalies", "Fenêtres anormales consécutives.")
FEATURE_VALUE = Gauge("ml_detector_feature", "Dernière valeur de feature.", ["feature"])
EVENTS_SENT = Counter("ml_detector_events_total", "Événements envoyés.", ["result"])
COLLECT_ERRORS = Counter("ml_detector_collect_errors_total", "Échecs de collecte Prometheus.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DETECTOR_", extra="ignore")

    prometheus_url: str = "http://prometheus:9090"
    remediation_url: str = "http://remediation:8000"
    event_token: str | None = None
    event_token_file: Path | None = None
    model_path: Path = Path("/opt/detector/models/isolation_forest.joblib")
    interval_seconds: float = 5.0
    min_send_interval_seconds: float = 5.0
    metrics_port: int = 8000
    log_level: str = "INFO"

    def token(self) -> str | None:
        if self.event_token:
            return self.event_token
        if self.event_token_file and self.event_token_file.is_file():
            return self.event_token_file.read_text(encoding="utf-8").strip()
        return None


class Detector:
    def __init__(
        self,
        settings: Settings,
        collector: PrometheusCollector,
        sender: httpx.Client,
    ) -> None:
        self.settings = settings
        self.collector = collector
        self.sender = sender
        self.bundle: ModelBundle | None = None
        self._model_mtime: float | None = None
        self.consecutive = 0
        self._last_sent = 0.0

    def reload_model_if_changed(self) -> None:
        path = self.settings.model_path
        if not path.is_file():
            if self.bundle is not None or self._model_mtime is None:
                logger.warning("detector.model_missing", extra={"path": str(path)})
            self.bundle, self._model_mtime = None, -1.0
            MODEL_LOADED.set(0)
            return
        mtime = path.stat().st_mtime
        if mtime == self._model_mtime:
            return
        try:
            self.bundle = load(path)
        except Exception:
            logger.exception("detector.model_load_failed")
            self.bundle = None
            MODEL_LOADED.set(0)
            return
        self._model_mtime = mtime
        MODEL_LOADED.set(1)
        MODEL_SYNTHETIC.set(1 if self.bundle.metadata.trained_on_synthetic else 0)
        logger.info(
            "detector.model_loaded",
            extra={
                "model_version": self.bundle.metadata.model_version,
                "trained_on_synthetic": self.bundle.metadata.trained_on_synthetic,
            },
        )

    def step(self) -> None:
        self.reload_model_if_changed()
        try:
            observation = self.collector.snapshot()
        except CollectError as exc:
            COLLECT_ERRORS.inc()
            logger.warning("detector.collect_failed", extra={"error": str(exc)})
            return
        for feature in FEATURES:
            value = observation.get(feature)
            if value is not None and value == value:
                FEATURE_VALUE.labels(feature).set(value)
        if self.bundle is None:
            return

        prediction = score(self.bundle, observation)
        self.consecutive = self.consecutive + 1 if prediction.is_anomaly else 0
        ANOMALY_SCORE.set(prediction.score)
        IS_ANOMALY.set(1 if prediction.is_anomaly else 0)
        CONSECUTIVE.set(self.consecutive)
        if not prediction.is_anomaly:
            return
        if time.monotonic() - self._last_sent < self.settings.min_send_interval_seconds:
            return
        event = build_event(self.bundle, observation, prediction, self.consecutive, datetime.now(UTC))
        self.send(event.model_dump(mode="json"))

    def send(self, payload: dict) -> None:
        token = self.settings.token()
        if not token:
            EVENTS_SENT.labels("no_token").inc()
            logger.error("detector.no_event_token")
            return
        try:
            response = self.sender.post("/events", json=payload, headers={"X-Resilience-Token": token})
            response.raise_for_status()
            self._last_sent = time.monotonic()
            EVENTS_SENT.labels("accepted").inc()
            logger.info(
                "detector.event_sent",
                extra={"event_id": payload["event_id"], "decision": response.json().get("outcome")},
            )
        except httpx.HTTPError as exc:
            EVENTS_SENT.labels("error").inc()
            logger.warning("detector.event_failed", extra={"error": str(exc)})


def _configure_logging(level: str) -> None:
    class Json(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            base = {
                "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname.lower(),
                "service": "ml-detector",
                "msg": record.getMessage(),
            }
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k in {"path", "error", "event_id", "decision", "model_version", "trained_on_synthetic"}
            }
            return json.dumps(base | extra, default=str, ensure_ascii=False)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(Json())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> int:
    settings = Settings()
    _configure_logging(settings.log_level)
    start_http_server(settings.metrics_port)
    detector = Detector(
        settings,
        PrometheusCollector(settings.prometheus_url),
        httpx.Client(base_url=settings.remediation_url, timeout=3.0),
    )
    logger.info("detector.started", extra={"path": str(settings.model_path)})
    while True:
        started = time.monotonic()
        detector.step()
        time.sleep(max(0.0, settings.interval_seconds - (time.monotonic() - started)))


if __name__ == "__main__":
    raise SystemExit(main())
