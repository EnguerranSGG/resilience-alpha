"""Entraînement d'un Isolation Forest et sauvegarde joblib.

Exemples ::

    # Jeu réel enregistré avec anomaly_detection.collect (recommandé)
    python -m anomaly_detection.train --data data/raw/normal.csv data/raw/attack.csv

    # Amorçage de la chaîne avec des données SYNTHÉTIQUES (modèle marqué comme tel)
    python -m anomaly_detection.train --synthetic

Le modèle est entraîné sur les lignes **normales** du jeu d'entraînement
(détection de nouveauté) ; les jeux de validation et de test servent à mesurer
la précision, le rappel, le F1 et les faux positifs lorsque des étiquettes existent.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from anomaly_detection import synthetic
from anomaly_detection.evaluate import classification_report
from anomaly_detection.features import FEATURES, LABEL_COLUMN, SYNTHETIC_COLUMN
from anomaly_detection.model import ModelBundle, ModelMetadata, load, save
from anomaly_detection.preprocess import chronological_split, clean

__all__ = ["DEFAULT_MODEL_PATH", "ModelBundle", "ModelMetadata", "load", "save", "train"]

DEFAULT_MODEL_PATH = Path("models/isolation_forest.joblib")


def train(
    frame: pd.DataFrame,
    contamination: float | str = "auto",
    n_estimators: int = 200,
    seed: int = 42,
    data_sources: list[str] | None = None,
) -> ModelBundle:
    data = clean(frame)
    train_df, val_df, test_df = chronological_split(data)
    has_labels = LABEL_COLUMN in data.columns
    fit_df = train_df[train_df[LABEL_COLUMN] == 0] if has_labels else train_df
    if len(fit_df) < 50:
        raise ValueError(f"trop peu d'observations normales pour entraîner ({len(fit_df)})")

    pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "forest",
                IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=seed),
            ),
        ]
    )
    pipeline.fit(fit_df[list(FEATURES)])

    synthetic_flag = bool(data.get(SYNTHETIC_COLUMN, pd.Series([False])).astype(bool).any())
    quantiles = {f: {"p50": float(fit_df[f].quantile(0.5)), "p99": float(fit_df[f].quantile(0.99))} for f in FEATURES}
    metadata = ModelMetadata(
        model_version=f"if-{datetime.now(UTC):%Y%m%d%H%M%S}",
        trained_at=datetime.now(UTC).isoformat(),
        trained_on_synthetic=synthetic_flag,
        features=list(FEATURES),
        n_training_samples=len(fit_df),
        contamination=contamination,
        threshold=0.0,
        sklearn_version=sklearn.__version__,
        training_quantiles=quantiles,
        data_sources=data_sources or [],
    )
    bundle = ModelBundle(pipeline, metadata)
    if has_labels:
        for name, split in (("validation", val_df), ("test", test_df)):
            if len(split):
                report = classification_report(split[LABEL_COLUMN], bundle.predict(split))
                metadata.evaluation[name] = report.as_dict()
    return bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Entraîner le détecteur Isolation Forest")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", type=Path, nargs="+", help="CSV issus de anomaly_detection.collect")
    source.add_argument("--synthetic", action="store_true", help="Données SYNTHÉTIQUES (tests)")
    parser.add_argument("--out", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--contamination", default="auto")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    if args.synthetic:
        frame, sources = synthetic.generate(seed=args.seed), ["synthetic.generate"]
    else:
        frame = pd.concat([pd.read_csv(p) for p in args.data], ignore_index=True)
        sources = [str(p) for p in args.data]
    contamination = args.contamination if args.contamination == "auto" else float(args.contamination)
    bundle = train(frame, contamination=contamination, seed=args.seed, data_sources=sources)
    save(bundle, args.out)
    print(json.dumps(asdict(bundle.metadata), indent=2, ensure_ascii=False))
    if bundle.metadata.trained_on_synthetic:
        print("\n⚠️  Modèle entraîné sur des données SYNTHÉTIQUES : non représentatif de la plateforme.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
