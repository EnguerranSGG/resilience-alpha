"""Artefact de modèle sérialisé (joblib) et métadonnées associées.

Défini hors de ``train.py`` pour que les classes soient importables sous un nom
stable (``anomaly_detection.model``) quel que soit le point d'entrée.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from anomaly_detection.features import FEATURES


@dataclass
class ModelMetadata:
    model_version: str
    trained_at: str
    trained_on_synthetic: bool
    features: list[str]
    n_training_samples: int
    contamination: float | str
    threshold: float
    sklearn_version: str
    training_quantiles: dict[str, dict[str, float]]
    evaluation: dict[str, Any] = field(default_factory=dict)
    data_sources: list[str] = field(default_factory=list)


@dataclass
class ModelBundle:
    pipeline: Pipeline
    metadata: ModelMetadata

    def scores(self, frame: pd.DataFrame) -> pd.Series:
        """Score ``decision_function`` : négatif = atypique."""
        return pd.Series(self.pipeline.decision_function(frame[list(FEATURES)]), index=frame.index)

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        return (self.scores(frame) < self.metadata.threshold).astype(int)


def save(bundle: ModelBundle, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    joblib.dump(bundle, tmp)
    tmp.replace(path)
    path.with_suffix(".json").write_text(
        json.dumps(asdict(bundle.metadata), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path


def load(path: Path) -> ModelBundle:
    # joblib/pickle : ne charger que des modèles produits localement par l'équipe.
    bundle = joblib.load(path)
    if not isinstance(bundle, ModelBundle):
        raise TypeError(f"{path} ne contient pas un ModelBundle")
    return bundle
