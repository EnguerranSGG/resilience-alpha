"""Politique de décision : quand une anomalie ML justifie-t-elle une action ?

Une mitigation n'est décidée que si **toutes** les conditions suivantes sont réunies :

1. l'action recommandée (s'il y en a une) appartient à la liste blanche ;
2. le modèle est accepté (modèle synthétique refusé par défaut) ;
3. le score franchit le seuil de la politique (pas seulement celui du détecteur) ;
4. l'anomalie persiste sur un nombre minimal de fenêtres consécutives ;
5. une corroboration indépendante existe : dégradation mesurée par Prometheus
   **ou** événements de sécurité relevés par Loki (désactivable pour les tests).

L'action exécutée est déterminée par le **type** d'événement, jamais par une
chaîne fournie par le producteur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from remediation_engine.config import PolicySettings
from remediation_engine.signals import DegradationReport, SecurityReport
from resilience_contracts import AnomalyEvent, AnomalyType, RecommendedAction


class Outcome(StrEnum):
    REJECT = "REJECT"
    IGNORE = "IGNORE"
    OBSERVE = "OBSERVE"
    MITIGATE = "MITIGATE"


ACTION_FOR_TYPE: dict[AnomalyType, RecommendedAction] = {
    AnomalyType.DOS_SUSPECTED: RecommendedAction.ENABLE_RATE_LIMIT,
}


@dataclass(frozen=True)
class Decision:
    outcome: Outcome
    action: RecommendedAction | None = None
    reasons: list[str] = field(default_factory=list)


def is_degraded(report: DegradationReport, policy: PolicySettings) -> bool:
    if not report.available:
        return False
    latency = report.latency_p95_ms or 0.0
    errors = report.error_rate or 0.0
    return latency >= policy.latency_p95_ms_threshold or errors >= policy.error_rate_threshold


def has_security_signal(report: SecurityReport, policy: PolicySettings) -> bool:
    return bool(report.available and (report.blocked_requests_1m or 0) >= policy.security_events_threshold)


def decide(
    event: AnomalyEvent,
    policy: PolicySettings,
    degradation: DegradationReport,
    security: SecurityReport,
) -> Decision:
    reasons: list[str] = []
    recommended = event.recommended_action
    if recommended is not RecommendedAction.NONE and recommended not in policy.allowed_actions:
        return Decision(Outcome.REJECT, reasons=[f"action recommandée non autorisée : {recommended}"])

    if event.trained_on_synthetic and not policy.accept_synthetic_model:
        return Decision(
            Outcome.OBSERVE,
            reasons=["modèle entraîné sur données synthétiques : refusé par la politique"],
        )

    if not event.is_anomaly or event.anomaly_score > policy.score_threshold:
        return Decision(
            Outcome.IGNORE,
            reasons=[f"score {event.anomaly_score:.3f} > seuil {policy.score_threshold:.3f}"],
        )

    consecutive = event.window.consecutive_anomalous_windows if event.window else 1
    if consecutive < policy.min_consecutive_windows:
        return Decision(
            Outcome.OBSERVE,
            reasons=[f"persistance insuffisante : {consecutive}/{policy.min_consecutive_windows}"],
        )
    reasons.append(f"persistance {consecutive} fenêtres")

    degraded = is_degraded(degradation, policy)
    security_signal = has_security_signal(security, policy)
    reasons.append(
        f"dégradation={'oui' if degraded else 'non'}"
        f" (p95={degradation.latency_p95_ms}, erreurs={degradation.error_rate},"
        f" mesure={'ok' if degradation.available else 'indisponible'})"
    )
    reasons.append(
        f"sécurité={'oui' if security_signal else 'non'}"
        f" (bloquées_1m={security.blocked_requests_1m},"
        f" mesure={'ok' if security.available else 'indisponible'})"
    )
    if policy.require_corroboration and not (degraded or security_signal):
        return Decision(Outcome.OBSERVE, reasons=[*reasons, "aucune corroboration indépendante"])

    action = ACTION_FOR_TYPE.get(event.type)
    if action is None or action not in policy.allowed_actions:
        return Decision(Outcome.OBSERVE, reasons=[*reasons, f"aucune action automatique pour {event.type}"])
    return Decision(Outcome.MITIGATE, action=action, reasons=reasons)
