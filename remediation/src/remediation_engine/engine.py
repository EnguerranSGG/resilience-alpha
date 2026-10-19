"""Orchestrateur : relie décision, machine à états, exécution et vérification."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from remediation_engine import metrics
from remediation_engine.config import PolicySettings, Settings
from remediation_engine.decision_engine import Decision, Outcome, decide
from remediation_engine.executor import PROFILE_AFTER_ACTION, ActionExecutor, ExecutionResult
from remediation_engine.incidents import Incident, IncidentStore
from remediation_engine.signals import DegradationProbe, SecuritySignalSource
from remediation_engine.state_machine import StateMachine, Transition
from remediation_engine.verification import BusinessVerifier, VerificationResult
from resilience_contracts import (
    AnomalyEvent,
    RecommendedAction,
    RemediationState,
    RemediationStatusView,
)

logger = logging.getLogger(__name__)
State = RemediationState


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RemediationEngine:
    def __init__(
        self,
        settings: Settings,
        policy: PolicySettings,
        executor: ActionExecutor,
        verifier: BusinessVerifier,
        degradation: DegradationProbe,
        security: SecuritySignalSource,
        store: IncidentStore,
        *,
        synchronous: bool = False,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.settings = settings
        self.policy = policy
        self.executor = executor
        self.verifier = verifier
        self.degradation = degradation
        self.security = security
        self.store = store
        self.synchronous = synchronous
        self.clock = clock
        self.machine = StateMachine(on_transition=self._on_transition)
        self.active_profile = "normal"
        self.current: Incident | None = None
        self._lock = threading.RLock()
        self._busy = False
        metrics.set_state(self.machine.state)
        metrics.set_profile(self.active_profile)
        metrics.EXECUTION_SIMULATED.set(1 if executor.mode.value == "simulated" else 0)

    # ------------------------------------------------------------------ vues
    @property
    def state(self) -> RemediationState:
        return self.machine.state

    def status(self) -> RemediationStatusView:
        return RemediationStatusView(
            state=self.machine.state,
            execution_mode=self.executor.mode,
            active_profile=self.active_profile,
            last_transition_at=self.machine.changed_at,
            current_incident_id=self.current.incident_id if self.current else None,
        )

    def adopt_observed_profile(self, profile: str | None) -> None:
        """Reprend au démarrage le profil réellement appliqué par la passerelle.

        Aucune action n'est déclenchée : si la passerelle est restée en mitigation
        (moteur redémarré en cours d'incident), la restauration reste une décision opérateur.
        """
        if profile is None or profile == self.active_profile:
            return
        self.active_profile = profile
        metrics.set_profile(profile)
        logger.warning(
            "remediation.profile_adopted",
            extra={
                "event": "remediation.profile_adopted",
                "profile": profile,
                "hint": "profil hérité d'une exécution précédente ; restauration : make gateway-restore",
            },
        )

    # ------------------------------------------------------------ transitions
    def _on_transition(self, transition: Transition) -> None:
        metrics.set_state(transition.target)
        logger.info(
            "remediation.transition",
            extra={
                "event": "remediation.transition",
                "from": transition.source.value,
                "to": transition.target.value,
                "reason": transition.reason,
                "incident_id": self.current.incident_id if self.current else None,
            },
        )
        if self.current:
            self.current.state = transition.target
            self.store.record(
                self.current,
                "transition",
                f"{transition.source} → {transition.target} : {transition.reason}",
            )

    def _close_current(self, message: str) -> None:
        if self.current:
            self.current.closed_at = self.clock()
            self.store.record(self.current, "closed", message)
            self.current = None

    # --------------------------------------------------------------- événements
    def handle_event(self, event: AnomalyEvent) -> Decision:
        with self._lock:
            guard = self._guard()
            if guard:
                if self.current:
                    self.current.last_anomaly_at = self.clock()
                metrics.EVENTS.labels(Outcome.IGNORE.value).inc()
                return Decision(Outcome.IGNORE, reasons=[guard])

            decision = decide(event, self.policy, self.degradation.measure(), self.security.measure())
            metrics.EVENTS.labels(decision.outcome.value).inc()
            logger.info(
                "remediation.decision",
                extra={
                    "event": "remediation.decision",
                    "event_id": event.event_id,
                    "outcome": decision.outcome.value,
                    "reasons": decision.reasons,
                    "anomaly_score": event.anomaly_score,
                },
            )
            if decision.outcome in (Outcome.REJECT, Outcome.IGNORE):
                return decision

            incident = self._ensure_incident(event)
            incident.last_anomaly_at = self.clock()
            self.store.record(
                incident,
                "decision",
                f"{event.event_id} → {decision.outcome} ({'; '.join(decision.reasons)})",
            )
            if decision.outcome is Outcome.OBSERVE:
                if self.machine.state is State.NORMAL:
                    self.machine.transition(State.SUSPECT, "anomalie non confirmée")
                return decision

            assert decision.action is not None
            incident.action = decision.action.value
            incident.attempts += 1
            incident.last_attempt_at = self.clock()
            self.machine.transition(State.MITIGATING, f"anomalie confirmée → {decision.action}")
            self._run(lambda: self._mitigate(incident, decision.action))
            return decision

    def _guard(self) -> str | None:
        state = self.machine.state
        if self._busy or state is State.MITIGATING:
            return "opération de remédiation déjà en cours : action non répétée"
        if state is State.RECOVERED:
            return "mitigation active et service vérifié : action non répétée"
        if state is State.FAILED and self.current:
            if self.current.attempts >= self.settings.max_attempts:
                return "nombre maximal de tentatives atteint : escalade opérateur (PCA/PRA)"
            last = self.current.last_attempt_at
            if last and (self.clock() - last).total_seconds() < self.settings.retry_cooldown_seconds:
                return "délai avant nouvelle tentative non écoulé"
        return None

    def _ensure_incident(self, event: AnomalyEvent) -> Incident:
        if self.current is None:
            self.current = self.store.open(
                Incident(
                    trigger_event_id=event.event_id,
                    execution_mode=self.executor.mode,
                    first_anomaly_at=event.window.start if event.window else event.timestamp,
                )
            )
            self.store.record(self.current, "opened", f"déclenché par {event.event_id}")
        return self.current

    def _run(self, job: Callable[[], None]) -> None:
        self._busy = True

        def wrapper() -> None:
            try:
                job()
            except Exception:
                logger.exception("remediation.job_crashed")
                with self._lock:
                    if self.machine.can(State.FAILED):
                        self.machine.transition(State.FAILED, "erreur interne du moteur")
            finally:
                self._busy = False

        if self.synchronous:
            wrapper()
        else:
            threading.Thread(target=wrapper, name="remediation-job", daemon=True).start()

    # --------------------------------------------------------------- actions
    def _execute(self, action: RecommendedAction, request_id: str) -> ExecutionResult:
        result = self.executor.execute(action, request_id)
        metrics.ACTIONS.labels(action.value, "success" if result.success else "failure", result.mode.value).inc()
        return result

    def _verify(self) -> VerificationResult:
        result = self.verifier.verify()
        metrics.VERIFICATIONS.labels("passed" if result.passed else "failed").inc()
        return result

    def _mitigate(self, incident: Incident, action: RecommendedAction) -> None:
        request_id = f"{incident.incident_id}-{incident.attempts}"
        result = self._execute(action, request_id)
        mode_note = " [SIMULATION]" if result.mode.value == "simulated" else ""
        self.store.record(incident, "action", f"{action} : {result.detail}{mode_note}")
        with self._lock:
            if not result.success:
                self.machine.transition(State.FAILED, f"échec de l'action {action}")
                return
            self.active_profile = PROFILE_AFTER_ACTION[action]
            metrics.set_profile(self.active_profile)

        verification = self._verify()
        self.store.record(incident, "verification", " | ".join(verification.steps))
        with self._lock:
            incident.verification_passed = verification.passed
            if not verification.passed:
                self.machine.transition(State.FAILED, "vérification métier en échec")
                return
            incident.recovered_at = self.clock()
            metrics.RECOVERY_SECONDS.observe((incident.recovered_at - incident.opened_at).total_seconds())
            self.machine.transition(State.RECOVERED, "transaction de contrôle réussie")

    def _restore(self, incident: Incident) -> None:
        request_id = f"{incident.incident_id}-restore"
        result = self._execute(RecommendedAction.RESTORE_NORMAL_PROFILE, request_id)
        self.store.record(incident, "action", f"RESTORE_NORMAL_PROFILE : {result.detail}")
        if not result.success:
            # Le profil de mitigation reste actif : situation sûre, nouvelle tentative plus tard.
            incident.recovered_at = self.clock()
            return
        with self._lock:
            self.active_profile = "normal"
            metrics.set_profile(self.active_profile)
            self.machine.transition(State.NORMAL, "stabilité confirmée, profil normal restauré")
            self._close_current("incident clos")

    # ------------------------------------------------------------- périodique
    def tick(self) -> None:
        with self._lock:
            if self._busy or self.current is None:
                return
            now = self.clock()
            quiet = (now - self.current.last_anomaly_at).total_seconds()
            state = self.machine.state
            if state is State.SUSPECT and quiet >= self.settings.suspect_timeout_seconds:
                self.machine.transition(State.NORMAL, "anomalie non confirmée dans le délai")
                self._close_current("clos sans action")
            elif state is State.RECOVERED and self.current.recovered_at:
                stable = (now - self.current.recovered_at).total_seconds()
                if min(stable, quiet) >= self.settings.restore_after_seconds:
                    incident = self.current
                    self._run(lambda: self._restore(incident))
