from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from resilience_contracts import RemediationState

STATE = Gauge("remediation_state", "1 pour l'état courant du moteur.", ["state"])
ACTIVE_PROFILE = Gauge("remediation_active_profile", "Profil NGINX demandé en dernier.", ["profile"])
EXECUTION_SIMULATED = Gauge("remediation_executor_simulated", "1 si l'exécuteur est en mode SIMULATION.")
EVENTS = Counter("remediation_events_total", "Événements ML reçus par décision.", ["outcome"])
ACTIONS = Counter("remediation_actions_total", "Actions exécutées.", ["action", "result", "mode"])
VERIFICATIONS = Counter("remediation_verifications_total", "Vérifications métier.", ["result"])
RECOVERY_SECONDS = Histogram(
    "remediation_recovery_seconds",
    "Durée entre ouverture d'incident et rétablissement vérifié (MTTR).",
    buckets=(5, 10, 20, 30, 45, 60, 90, 120, 180, 300, 600),
)


def set_state(state: RemediationState) -> None:
    for candidate in RemediationState:
        STATE.labels(candidate.value).set(1 if candidate is state else 0)


def set_profile(profile: str) -> None:
    for candidate in ("normal", "mitigation"):
        ACTIVE_PROFILE.labels(candidate).set(1 if candidate == profile else 0)
