"""T07 (modèle entraîné et rechargé) et T08 (événement conforme au contrat).

Les tests utilisent des données SYNTHÉTIQUES : ils valident la chaîne logicielle,
pas la qualité de détection sur la plateforme réelle.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest

from anomaly_detection import synthetic
from anomaly_detection.collect import CollectError, PrometheusCollector
from anomaly_detection.evaluate import classification_report
from anomaly_detection.features import FEATURES
from anomaly_detection.main import Detector, Settings
from anomaly_detection.model import load, save
from anomaly_detection.predict import build_event, score
from anomaly_detection.preprocess import chronological_split, clean, vectorize
from anomaly_detection.train import train
from resilience_contracts import AnomalyEvent, AnomalyType, RecommendedAction

NORMAL = {"request_rate": 4, "latency_p95": 60, "error_rate": 0.0, "cpu_usage": 0.05, "active_requests": 1}
ATTACK = {"request_rate": 95, "latency_p95": 1500, "error_rate": 0.2, "cpu_usage": 0.9, "active_requests": 30}


@pytest.fixture(scope="module")
def bundle():
    return train(synthetic.generate(n_samples=1500, seed=7))


def test_synthetic_data_is_flagged() -> None:
    frame = synthetic.generate(n_samples=200)
    assert frame["is_synthetic"].all()
    assert set(frame["label"].unique()) <= {0, 1}


def test_clean_handles_nan_inf_and_bounds() -> None:
    raw = pd.DataFrame(
        {
            "request_rate": [1, np.nan],
            "latency_p95": [np.inf, 10],
            "error_rate": [2, -1],
            "cpu_usage": ["x", 0.1],
            "active_requests": [0, 1],
        }
    )
    cleaned = clean(raw)
    assert not cleaned[list(FEATURES)].isna().any().any()
    assert cleaned["error_rate"].between(0, 1).all()


def test_chronological_split_keeps_order() -> None:
    frame = clean(synthetic.generate(n_samples=100))
    train_df, val_df, test_df = chronological_split(frame)
    assert len(train_df) == 60 and len(val_df) == 20 and len(test_df) == 20
    assert train_df["timestamp"].max() < val_df["timestamp"].min() < test_df["timestamp"].min()


def test_train_save_and_load_roundtrip(bundle, tmp_path: Path) -> None:
    path = save(bundle, tmp_path / "model.joblib")
    loaded = load(path)
    assert loaded.metadata.trained_on_synthetic is True
    assert (tmp_path / "model.json").is_file()
    frame = vectorize(NORMAL)
    assert loaded.scores(frame).iloc[0] == pytest.approx(bundle.scores(frame).iloc[0])


def test_model_separates_obvious_cases(bundle) -> None:
    assert not score(bundle, NORMAL).is_anomaly
    assert score(bundle, ATTACK).is_anomaly
    assert score(bundle, ATTACK).score < score(bundle, NORMAL).score


def test_evaluation_metrics_are_reported(bundle) -> None:
    test_report = bundle.metadata.evaluation["test"]
    assert {"precision", "recall", "f1", "false_positives", "false_positive_rate"} <= set(test_report)


def test_classification_report_values() -> None:
    report = classification_report(np.array([0, 0, 1, 1]), np.array([0, 1, 1, 0]))
    counts = (report.true_negatives, report.false_positives, report.false_negatives, report.true_positives)
    assert counts == (1, 1, 1, 1)
    assert report.precision == 0.5 and report.recall == 0.5 and report.false_positive_rate == 0.5


def test_event_matches_contract(bundle) -> None:
    prediction = score(bundle, ATTACK)
    event = build_event(bundle, ATTACK, prediction, consecutive=3, now=datetime.now(UTC))
    reparsed = AnomalyEvent.model_validate(event.model_dump(mode="json"))
    assert reparsed.type is AnomalyType.DOS_SUSPECTED
    assert reparsed.recommended_action is RecommendedAction.ENABLE_RATE_LIMIT
    assert reparsed.trained_on_synthetic is True
    assert reparsed.window and reparsed.window.consecutive_anomalous_windows == 3


def test_event_with_missing_metrics_is_valid(bundle) -> None:
    observation = NORMAL | {"latency_p95": math.nan}
    event = build_event(bundle, observation, score(bundle, observation), 1, datetime.now(UTC))
    assert event.metrics.latency_p95_ms is None


def _prom_handler(values: dict[str, float]):
    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params["query"]
        name = next(f for f in FEATURES if f.split("_")[0] in query)
        result = [{"metric": {}, "value": [0, str(values[name])]}]
        return httpx.Response(200, json={"status": "success", "data": {"result": result}})

    return handler


def test_collector_snapshot_parses_prometheus() -> None:
    collector = PrometheusCollector("http://prom", transport=httpx.MockTransport(_prom_handler(ATTACK)))
    assert collector.snapshot()["request_rate"] == 95


def test_collector_raises_on_error() -> None:
    collector = PrometheusCollector("http://prom", transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    with pytest.raises(CollectError):
        collector.snapshot()


def test_detector_without_model_sends_nothing(tmp_path: Path) -> None:
    sent: list[httpx.Request] = []
    detector = Detector(
        Settings(model_path=tmp_path / "absent.joblib", event_token="t"),
        PrometheusCollector("http://prom", transport=httpx.MockTransport(_prom_handler(ATTACK))),
        httpx.Client(
            base_url="http://rem",
            transport=httpx.MockTransport(lambda r: sent.append(r) or httpx.Response(202, json={})),
        ),
    )
    detector.step()
    assert sent == []


def test_detector_sends_event_on_anomaly(bundle, tmp_path: Path) -> None:
    path = save(bundle, tmp_path / "m.joblib")
    sent: list[httpx.Request] = []

    def remediation(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(202, json={"outcome": "OBSERVE"})

    detector = Detector(
        Settings(model_path=path, event_token="t", min_send_interval_seconds=0),
        PrometheusCollector("http://prom", transport=httpx.MockTransport(_prom_handler(ATTACK))),
        httpx.Client(base_url="http://rem", transport=httpx.MockTransport(remediation)),
    )
    detector.step()
    detector.step()
    assert len(sent) == 2
    assert sent[0].headers["X-Resilience-Token"] == "t"
    assert AnomalyEvent.model_validate_json(sent[1].content).window.consecutive_anomalous_windows == 2
