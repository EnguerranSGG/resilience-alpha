"""Contrats partagés RESILIENCE-ALPHA.

Toute modification incompatible d'un contrat impose d'incrémenter ``SCHEMA_VERSION``
et de régénérer les schémas JSON publiés dans ``docs/contracts/``.
"""

from resilience_contracts.events import (
    SCHEMA_VERSION,
    AnomalyEvent,
    AnomalyType,
    DetectionWindow,
    MetricsSnapshot,
    RecommendedAction,
)
from resilience_contracts.remediation import (
    ExecutionMode,
    IncidentView,
    RemediationState,
    RemediationStatusView,
)

__all__ = [
    "SCHEMA_VERSION",
    "AnomalyEvent",
    "AnomalyType",
    "DetectionWindow",
    "ExecutionMode",
    "IncidentView",
    "MetricsSnapshot",
    "RecommendedAction",
    "RemediationState",
    "RemediationStatusView",
]
