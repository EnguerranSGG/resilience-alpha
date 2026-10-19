"""Collecte des features depuis l'API HTTP Prometheus.

Deux usages :

* ``PrometheusCollector.snapshot()`` : valeur instantanée (inférence en ligne) ;
* ``PrometheusCollector.range()`` : série temporelle pour constituer un jeu de
  données **réel** (enregistrement d'une période normale ou d'un essai de charge).

CLI d'enregistrement d'un jeu de données étiqueté ::

    python -m anomaly_detection.collect --minutes 20 --label 0 --out data/raw/normal-$(date +%s).csv
"""

from __future__ import annotations

import argparse
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

from anomaly_detection.features import FEATURES, LABEL_COLUMN, PROMQL, SYNTHETIC_COLUMN


class CollectError(RuntimeError):
    pass


def _to_float(raw: str) -> float:
    value = float(raw)
    return math.nan if math.isinf(value) else value


class PrometheusCollector:
    def __init__(self, base_url: str, timeout: float = 3.0, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def _get(self, path: str, params: dict[str, str]) -> list[dict]:
        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CollectError(str(exc)) from exc
        if payload.get("status") != "success":
            raise CollectError(payload.get("error", "réponse Prometheus invalide"))
        return payload["data"]["result"]

    def snapshot(self) -> dict[str, float]:
        """Valeurs instantanées ; ``nan`` si la série est absente."""
        values: dict[str, float] = {}
        for feature in FEATURES:
            result = self._get("/api/v1/query", {"query": PROMQL[feature]})
            values[feature] = _to_float(result[0]["value"][1]) if result else math.nan
        return values

    def range(self, start: datetime, end: datetime, step_seconds: int = 5) -> pd.DataFrame:
        frames = []
        for feature in FEATURES:
            result = self._get(
                "/api/v1/query_range",
                {
                    "query": PROMQL[feature],
                    "start": f"{start.timestamp():.0f}",
                    "end": f"{end.timestamp():.0f}",
                    "step": f"{step_seconds}s",
                },
            )
            points = result[0]["values"] if result else []
            frames.append(
                pd.Series(
                    {datetime.fromtimestamp(float(t), UTC): _to_float(v) for t, v in points},
                    name=feature,
                    dtype="float64",
                )
            )
        frame = pd.concat(frames, axis=1).sort_index()
        frame.index.name = "timestamp"
        return frame.reset_index()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exporter un jeu de features réel depuis Prometheus")
    parser.add_argument("--prometheus", default="http://localhost:9090")
    parser.add_argument("--minutes", type=int, default=15)
    parser.add_argument("--step", type=int, default=5)
    parser.add_argument("--label", type=int, choices=(0, 1), help="Étiquette de la période (facultatif)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    end = datetime.now(UTC)
    frame = PrometheusCollector(args.prometheus).range(end - timedelta(minutes=args.minutes), end, args.step)
    frame[SYNTHETIC_COLUMN] = False
    if args.label is not None:
        frame[LABEL_COLUMN] = args.label
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(f"{len(frame)} lignes réelles écrites dans {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
