"""Métriques de classification sur des séquences étiquetées (0 = normal, 1 = anomalie)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


@dataclass(frozen=True)
class ClassificationReport:
    precision: float
    recall: float
    f1: float
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int
    false_positive_rate: float
    support: int

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def classification_report(y_true: np.ndarray, y_pred: np.ndarray) -> ClassificationReport:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    negatives = tn + fp
    return ClassificationReport(
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        true_negatives=int(tn),
        false_positives=int(fp),
        false_negatives=int(fn),
        true_positives=int(tp),
        false_positive_rate=float(fp / negatives) if negatives else 0.0,
        support=len(y_true),
    )
