"""⚠️ GÉNÉRATEUR DE DONNÉES SYNTHÉTIQUES — tests et amorçage uniquement.

Ces données ne proviennent PAS de la plateforme. Elles servent à tester la
chaîne (entraînement, sauvegarde, inférence, évaluation) avant la collecte
réelle. Toute ligne produite porte ``is_synthetic=True`` et tout modèle entraîné
dessus est marqué ``trained_on_synthetic=True`` ; le moteur de remédiation le
refuse par défaut.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from anomaly_detection.features import FEATURES, LABEL_COLUMN, SYNTHETIC_COLUMN


def generate(
    n_samples: int = 2_000,
    attack_ratio: float = 0.1,
    seed: int = 42,
    step_seconds: int = 5,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    labels = np.zeros(n_samples, dtype=int)
    n_attack = int(n_samples * attack_ratio)
    # Attaques regroupées en épisodes contigus (comme un vrai test de charge).
    episode = max(n_attack // 4, 1)
    starts = rng.choice(np.arange(n_samples // 5, n_samples - episode), size=4, replace=False)
    for start in starts:
        labels[start : start + episode] = 1

    normal = {
        "request_rate": rng.normal(4, 1.2, n_samples).clip(0),
        "latency_p95": rng.normal(60, 15, n_samples).clip(5),
        "error_rate": rng.beta(1, 300, n_samples),
        "cpu_usage": rng.normal(0.05, 0.02, n_samples).clip(0),
        "active_requests": rng.poisson(1, n_samples).astype(float),
    }
    attack = {
        "request_rate": rng.normal(90, 20, n_samples).clip(20),
        "latency_p95": rng.normal(1400, 400, n_samples).clip(300),
        "error_rate": rng.beta(4, 20, n_samples),
        "cpu_usage": rng.normal(0.8, 0.15, n_samples).clip(0),
        "active_requests": rng.poisson(30, n_samples).astype(float),
    }
    start_time = datetime(2026, 1, 1, tzinfo=UTC)
    frame = pd.DataFrame(
        {
            "timestamp": [start_time + timedelta(seconds=i * step_seconds) for i in range(n_samples)],
            **{f: np.where(labels == 1, attack[f], normal[f]) for f in FEATURES},
        }
    )
    frame[LABEL_COLUMN] = labels
    frame[SYNTHETIC_COLUMN] = True
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Générer un jeu SYNTHÉTIQUE (tests uniquement)")
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/synthetic/synthetic-features.csv"))
    args = parser.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    generate(args.samples, seed=args.seed).to_csv(args.out, index=False)
    print(f"Données SYNTHÉTIQUES écrites dans {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
