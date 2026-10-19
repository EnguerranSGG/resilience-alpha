import pytest

from remediation_engine.state_machine import ALLOWED_TRANSITIONS, InvalidTransitionError, StateMachine
from resilience_contracts import RemediationState as State


def test_every_state_has_transitions() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(State)


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (State.NORMAL, State.RECOVERED),
        (State.SUSPECT, State.RECOVERED),
        (State.MITIGATING, State.NORMAL),
        (State.RECOVERED, State.MITIGATING),
    ],
)
def test_forbidden_transitions(source: State, target: State) -> None:
    machine = StateMachine(state=source)
    with pytest.raises(InvalidTransitionError):
        machine.transition(target, "test")


def test_history_is_recorded() -> None:
    machine = StateMachine()
    machine.transition(State.MITIGATING, "confirmé")
    machine.transition(State.RECOVERED, "vérifié")
    assert [t.target for t in machine.history] == [State.MITIGATING, State.RECOVERED]
