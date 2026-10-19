"""Machine à états explicite du moteur de remédiation.

::

    NORMAL ──anomalie non confirmée──▶ SUSPECT ──délai sans confirmation──▶ NORMAL
      │                                  │
      └────────anomalie confirmée────────┴──▶ MITIGATING ──action + vérif OK──▶ RECOVERED
                                               │   ▲                              │
                                  échec action │   │ nouvelle tentative           │ restauration
                                  ou vérif     ▼   │ (si autorisée)               ▼ du profil normal
                                              FAILED                            NORMAL
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from resilience_contracts import RemediationState as State

ALLOWED_TRANSITIONS: dict[State, frozenset[State]] = {
    State.NORMAL: frozenset({State.SUSPECT, State.MITIGATING}),
    State.SUSPECT: frozenset({State.NORMAL, State.MITIGATING}),
    State.MITIGATING: frozenset({State.RECOVERED, State.FAILED}),
    State.RECOVERED: frozenset({State.NORMAL}),
    State.FAILED: frozenset({State.MITIGATING, State.NORMAL}),
}


class InvalidTransitionError(RuntimeError):
    pass


@dataclass
class Transition:
    source: State
    target: State
    reason: str
    at: datetime


@dataclass
class StateMachine:
    state: State = State.NORMAL
    changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    history: list[Transition] = field(default_factory=list)
    on_transition: Callable[[Transition], None] | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def can(self, target: State) -> bool:
        return target in ALLOWED_TRANSITIONS[self.state]

    def transition(self, target: State, reason: str) -> Transition:
        with self._lock:
            if not self.can(target):
                raise InvalidTransitionError(f"{self.state} → {target} interdit ({reason})")
            event = Transition(self.state, target, reason, datetime.now(UTC))
            self.state = target
            self.changed_at = event.at
            self.history.append(event)
            del self.history[:-200]
        if self.on_transition:
            self.on_transition(event)
        return event
