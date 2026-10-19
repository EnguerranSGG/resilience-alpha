"""Contrat d'événement d'anomalie émis par le détecteur ML (version 1.0).

Points de vigilance :

* ``recommended_action`` est une **recommandation**. Le moteur de remédiation
  ne l'exécute jamais telle quelle : il applique sa propre politique et sa
  propre liste blanche.
* ``anomaly_score`` suit la convention scikit-learn ``decision_function`` :
  plus le score est négatif, plus l'observation est atypique.
* Une anomalie statistique n'est pas la preuve d'une attaque.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

_IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]{1,64}$"


class AnomalyType(StrEnum):
    DOS_SUSPECTED = "DOS_SUSPECTED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"


class RecommendedAction(StrEnum):
    """Vocabulaire fermé des actions qu'un détecteur peut suggérer.

    La présence d'une valeur dans cette énumération ne signifie pas qu'elle est
    autorisée : l'autorisation relève de la politique du moteur de remédiation.
    """

    NONE = "NONE"
    ENABLE_RATE_LIMIT = "ENABLE_RATE_LIMIT"
    RESTORE_NORMAL_PROFILE = "RESTORE_NORMAL_PROFILE"
    RESTART_SERVICE = "RESTART_SERVICE"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MetricsSnapshot(_StrictModel):
    """Valeurs des features observées sur la fenêtre analysée."""

    request_rate: float | None = Field(default=None, ge=0, description="Requêtes HTTP par seconde.")
    latency_p95_ms: float | None = Field(default=None, ge=0, description="Latence p95 en millisecondes.")
    error_rate: float | None = Field(default=None, ge=0, le=1, description="Part des réponses HTTP 5xx.")
    cpu_usage: float | None = Field(default=None, ge=0, description="Secondes CPU consommées par seconde.")
    active_requests: float | None = Field(default=None, ge=0, description="Requêtes en cours de traitement.")


class DetectionWindow(_StrictModel):
    start: AwareDatetime
    end: AwareDatetime
    consecutive_anomalous_windows: int = Field(ge=0, le=10_000)


class AnomalyEvent(_StrictModel):
    schema_version: Literal["1.0"]
    event_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    type: AnomalyType
    timestamp: AwareDatetime
    source: str = Field(pattern=_IDENTIFIER_PATTERN)
    model: str = Field(pattern=_IDENTIFIER_PATTERN)
    model_version: str = Field(default="unknown", pattern=_IDENTIFIER_PATTERN)
    trained_on_synthetic: bool = Field(
        description="Vrai si le modèle a été entraîné sur des données synthétiques.",
    )
    anomaly_score: float = Field(ge=-1, le=1)
    threshold: float = Field(default=0.0, ge=-1, le=1)
    is_anomaly: bool = True
    window: DetectionWindow | None = None
    metrics: MetricsSnapshot
    recommended_action: RecommendedAction = RecommendedAction.NONE
