"""Nettoyage et préparation des observations."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from anomaly_detection.features import FEATURES

# Sans trafic, Prometheus renvoie NaN pour la latence (quantile sur 0 requête)
# et pour le taux d'erreur : l'absence de trafic est interprétée comme 0.
FILL_VALUES: dict[str, float] = {feature: 0.0 for feature in FEATURES}


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Colonnes attendues, valeurs numériques, bornes physiques, tri chronologique."""
    missing = [f for f in FEATURES if f not in frame.columns]
    if missing:
        raise ValueError(f"colonnes manquantes : {missing}")
    result = frame.copy()
    for feature in FEATURES:
        result[feature] = pd.to_numeric(result[feature], errors="coerce")
    result[list(FEATURES)] = result[list(FEATURES)].replace([np.inf, -np.inf], np.nan).fillna(FILL_VALUES).clip(lower=0)
    result["error_rate"] = result["error_rate"].clip(upper=1)
    if "timestamp" in result.columns:
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True)
        result = result.sort_values("timestamp").drop_duplicates("timestamp")
    return result.reset_index(drop=True)


def vectorize(observation: Mapping[str, float]) -> pd.DataFrame:
    """Une observation en ligne → DataFrame à une ligne, NaN remplacés."""
    row = {}
    for feature in FEATURES:
        value = observation.get(feature, math.nan)
        row[feature] = FILL_VALUES[feature] if value is None or math.isnan(value) else max(value, 0.0)
    return pd.DataFrame([row], columns=list(FEATURES))


def chronological_split(
    frame: pd.DataFrame, train: float = 0.6, validation: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Découpage temporel sans mélange (évite la fuite d'information entre périodes)."""
    if not 0 < train < 1 or not 0 <= validation < 1 or train + validation >= 1:
        raise ValueError("proportions invalides")
    n = len(frame)
    i_train, i_val = int(n * train), int(n * (train + validation))
    return frame.iloc[:i_train], frame.iloc[i_train:i_val], frame.iloc[i_val:]
