from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from remediation_engine.executor import ActionNotAllowedError, AnsibleExecutor, SimulatedExecutor
from resilience_contracts import RecommendedAction

REPO = Path(__file__).resolve().parents[2]
ANSIBLE_DIR = REPO / "infrastructure" / "ansible"


class FakeRunner:
    def __init__(self, returncode: int = 0, timeout: bool = False) -> None:
        self.returncode = returncode
        self.timeout = timeout
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append((cmd, kwargs))
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd, 1)
        return subprocess.CompletedProcess(cmd, self.returncode, "out", "err")


def _executor(runner: FakeRunner) -> AnsibleExecutor:
    return AnsibleExecutor(ANSIBLE_DIR, ANSIBLE_DIR / "inventory" / "remediation.yml", 30, runner=runner)


def test_mitigation_maps_to_fixed_playbook_without_shell() -> None:
    runner = FakeRunner()
    result = _executor(runner).execute(RecommendedAction.ENABLE_RATE_LIMIT, "inc-abc123-1")
    cmd, kwargs = runner.calls[0]
    assert result.success
    assert cmd[3].endswith("infrastructure/ansible/mitigate.yml")
    assert json.loads(cmd[5]) == {"request_id": "inc-abc123-1"}
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == 30


def test_playbook_failure_is_reported() -> None:
    result = _executor(FakeRunner(returncode=2)).execute(RecommendedAction.ENABLE_RATE_LIMIT, "inc-abc123-1")
    assert not result.success
    assert "2" in result.detail


def test_playbook_timeout_is_reported() -> None:
    result = _executor(FakeRunner(timeout=True)).execute(RecommendedAction.RESTORE_NORMAL_PROFILE, "inc-abc123-r")
    assert not result.success


@pytest.mark.parametrize("action", [RecommendedAction.RESTART_SERVICE, RecommendedAction.NONE])
def test_actions_outside_whitelist_are_refused(action: RecommendedAction) -> None:
    runner = FakeRunner()
    with pytest.raises(ActionNotAllowedError):
        _executor(runner).execute(action, "inc-abc123-1")
    with pytest.raises(ActionNotAllowedError):
        SimulatedExecutor().execute(action, "inc-abc123-1")
    assert runner.calls == []


@pytest.mark.parametrize("request_id", ["x", "a; rm -rf /", "../../etc/passwd", "a" * 65])
def test_request_id_injection_is_refused(request_id: str) -> None:
    with pytest.raises(ActionNotAllowedError):
        _executor(FakeRunner()).execute(RecommendedAction.ENABLE_RATE_LIMIT, request_id)


def test_playbooks_exist_for_every_whitelisted_action() -> None:
    for name in ("mitigate.yml", "restore.yml", "deploy.yml"):
        assert (ANSIBLE_DIR / name).is_file()
