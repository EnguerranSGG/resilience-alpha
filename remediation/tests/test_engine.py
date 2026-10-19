"""Comportement du moteur : décision, non-répétition, échecs, vérification, restauration."""

from __future__ import annotations

from collections.abc import Callable

from remediation_engine.decision_engine import Outcome
from remediation_engine.executor import SimulatedExecutor
from remediation_engine.signals import (
    DegradationReport,
    SecurityReport,
    StaticDegradationProbe,
    StaticSecuritySignals,
)
from resilience_contracts import RecommendedAction, RemediationState

State = RemediationState


def test_confirmed_anomaly_mitigates_and_verifies(make_engine, make_event, executor, gateway) -> None:
    engine = make_engine()
    decision = engine.handle_event(make_event())
    assert decision.outcome is Outcome.MITIGATE
    assert executor.calls[0][0] is RecommendedAction.ENABLE_RATE_LIMIT
    assert engine.state is State.RECOVERED
    assert engine.active_profile == "mitigation"
    assert "POST /api/payments" in gateway.calls
    assert engine.current is not None and engine.current.verification_passed is True


def test_unconfirmed_anomaly_does_not_remediate(make_engine, make_event, executor) -> None:
    engine = make_engine()
    event = make_event(
        window={
            "start": "2026-10-19T09:59:30Z",
            "end": "2026-10-19T10:00:00Z",
            "consecutive_anomalous_windows": 1,
        }
    )
    decision = engine.handle_event(event)
    assert decision.outcome is Outcome.OBSERVE
    assert engine.state is State.SUSPECT
    assert executor.calls == []


def test_no_corroboration_means_no_action(make_engine, make_event, executor) -> None:
    healthy = StaticDegradationProbe(DegradationReport(True, latency_p95_ms=40, error_rate=0.0))
    quiet = StaticSecuritySignals(SecurityReport(True, blocked_requests_1m=0))
    engine = make_engine(degradation=healthy, security=quiet)
    decision = engine.handle_event(make_event())
    assert decision.outcome is Outcome.OBSERVE
    assert "aucune corroboration indépendante" in decision.reasons
    assert executor.calls == []


def test_unavailable_signals_are_not_treated_as_degradation(make_engine, make_event, executor) -> None:
    engine = make_engine(
        degradation=StaticDegradationProbe(DegradationReport(False)),
        security=StaticSecuritySignals(SecurityReport(False)),
    )
    assert engine.handle_event(make_event()).outcome is Outcome.OBSERVE
    assert executor.calls == []


def test_security_signal_alone_can_corroborate(make_engine, make_event, executor) -> None:
    engine = make_engine(
        degradation=StaticDegradationProbe(DegradationReport(True, latency_p95_ms=50, error_rate=0)),
        security=StaticSecuritySignals(SecurityReport(True, blocked_requests_1m=500)),
    )
    assert engine.handle_event(make_event()).outcome is Outcome.MITIGATE


def test_unauthorized_recommended_action_is_rejected(make_engine, make_event, executor) -> None:
    engine = make_engine()
    decision = engine.handle_event(make_event(recommended_action="RESTART_SERVICE"))
    assert decision.outcome is Outcome.REJECT
    assert engine.state is State.NORMAL
    assert executor.calls == []


def test_synthetic_model_is_refused_by_default(make_engine, make_event, executor) -> None:
    engine = make_engine()
    decision = engine.handle_event(make_event(trained_on_synthetic=True))
    assert decision.outcome is Outcome.OBSERVE
    assert executor.calls == []


def test_score_above_threshold_is_ignored(make_engine, make_event, executor) -> None:
    engine = make_engine()
    assert engine.handle_event(make_event(anomaly_score=0.1)).outcome is Outcome.IGNORE
    assert engine.state is State.NORMAL


def test_actions_are_not_repeated(make_engine, make_event, executor) -> None:
    engine = make_engine()
    engine.handle_event(make_event())
    for _ in range(5):
        assert engine.handle_event(make_event()).outcome is Outcome.IGNORE
    assert len(executor.calls) == 1


def test_event_ignored_while_mitigation_in_progress(make_engine, make_event, executor) -> None:
    engine = make_engine()
    engine._busy = True  # mitigation en cours dans un autre thread
    decision = engine.handle_event(make_event())
    assert decision.outcome is Outcome.IGNORE
    assert executor.calls == []


def test_failed_playbook_leads_to_failed_state(make_engine, make_event) -> None:
    failing = SimulatedExecutor(failing_actions={RecommendedAction.ENABLE_RATE_LIMIT})
    engine = make_engine(executor=failing)
    engine.handle_event(make_event())
    assert engine.state is State.FAILED
    assert engine.active_profile == "normal"


def test_failed_state_retries_after_cooldown_then_escalates(make_engine, make_event, clock) -> None:
    failing = SimulatedExecutor(failing_actions={RecommendedAction.ENABLE_RATE_LIMIT})
    engine = make_engine(executor=failing)
    engine.handle_event(make_event())
    assert engine.handle_event(make_event()).outcome is Outcome.IGNORE  # cooldown
    clock.advance(11)
    assert engine.handle_event(make_event()).outcome is Outcome.MITIGATE  # 2e tentative
    clock.advance(11)
    decision = engine.handle_event(make_event())
    assert decision.outcome is Outcome.IGNORE
    assert "escalade" in decision.reasons[0]
    assert len(failing.calls) == 2


def test_failed_verification_leads_to_failed_state(make_engine, make_event, gateway) -> None:
    gateway.payment_status = "FAILED"
    engine = make_engine()
    engine.handle_event(make_event())
    assert engine.state is State.FAILED
    assert engine.current is not None and engine.current.verification_passed is False


def test_duplicate_on_replay_fails_verification(make_engine, make_event, gateway) -> None:
    gateway.duplicate_on_replay = True
    engine = make_engine()
    engine.handle_event(make_event())
    assert engine.state is State.FAILED


def test_unhealthy_gateway_fails_verification(make_engine, make_event, gateway) -> None:
    gateway.ready_status = 503
    engine = make_engine()
    engine.handle_event(make_event())
    assert engine.state is State.FAILED


def test_suspect_returns_to_normal_after_timeout(make_engine, make_event, clock) -> None:
    engine = make_engine()
    engine.handle_event(make_event(trained_on_synthetic=True))
    assert engine.state is State.SUSPECT
    clock.advance(61)
    engine.tick()
    assert engine.state is State.NORMAL
    assert engine.current is None


def test_restore_normal_profile_after_stability(make_engine, make_event, executor, clock) -> None:
    engine = make_engine()
    engine.handle_event(make_event())
    clock.advance(60)
    engine.tick()
    assert engine.state is State.RECOVERED  # pas encore stable
    clock.advance(61)
    engine.tick()
    assert engine.state is State.NORMAL
    assert engine.active_profile == "normal"
    assert [a for a, _ in executor.calls] == [
        RecommendedAction.ENABLE_RATE_LIMIT,
        RecommendedAction.RESTORE_NORMAL_PROFILE,
    ]


def test_timeline_records_full_chronology(make_engine: Callable, make_event: Callable) -> None:
    engine = make_engine()
    engine.handle_event(make_event())
    kinds = [entry["kind"] for entry in engine.store.recent()[0].timeline]
    assert kinds[:2] == ["opened", "decision"]
    assert {"action", "verification", "transition"} <= set(kinds)
    assert any("[SIMULATION]" in e["message"] for e in engine.store.recent()[0].timeline)
