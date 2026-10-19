"""Exécution des actions autorisées.

Garanties :

* l'action est une valeur d'énumération, jamais une chaîne libre ;
* chaque action correspond à **un** playbook fixe ; le profil NGINX ciblé est
  codé dans le playbook, pas transmis par l'appelant ;
* seul ``request_id`` (format contrôlé) est passé en variable ;
* ``subprocess`` est appelé sans shell, avec un délai maximal et un
  environnement minimal.

``SimulatedExecutor`` n'agit sur rien : il est signalé comme tel dans les logs,
les métriques, l'API et le dashboard.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from resilience_contracts import ExecutionMode, RecommendedAction

logger = logging.getLogger(__name__)

PLAYBOOKS: dict[RecommendedAction, str] = {
    RecommendedAction.ENABLE_RATE_LIMIT: "mitigate.yml",
    RecommendedAction.RESTORE_NORMAL_PROFILE: "restore.yml",
}
PROFILE_AFTER_ACTION: dict[RecommendedAction, str] = {
    RecommendedAction.ENABLE_RATE_LIMIT: "mitigation",
    RecommendedAction.RESTORE_NORMAL_PROFILE: "normal",
}
_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class ActionNotAllowedError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionResult:
    action: RecommendedAction
    success: bool
    mode: ExecutionMode
    detail: str
    duration_seconds: float


class ActionExecutor(Protocol):
    mode: ExecutionMode

    def execute(self, action: RecommendedAction, request_id: str) -> ExecutionResult: ...


def _validate(action: RecommendedAction, request_id: str) -> None:
    if action not in PLAYBOOKS:
        raise ActionNotAllowedError(f"action hors liste blanche : {action}")
    if not _REQUEST_ID.match(request_id):
        raise ActionNotAllowedError("request_id invalide")


class SimulatedExecutor:
    """Adaptateur de SIMULATION : n'applique aucune configuration."""

    mode = ExecutionMode.SIMULATED

    def __init__(self, failing_actions: set[RecommendedAction] | None = None) -> None:
        self.failing_actions = failing_actions or set()
        self.calls: list[tuple[RecommendedAction, str]] = []

    def execute(self, action: RecommendedAction, request_id: str) -> ExecutionResult:
        _validate(action, request_id)
        self.calls.append((action, request_id))
        success = action not in self.failing_actions
        logger.warning(
            "executor.simulated",
            extra={
                "event": "executor.simulated",
                "action": action.value,
                "request_id": request_id,
                "success": success,
                "note": "SIMULATION — aucune configuration n'a été modifiée",
            },
        )
        return ExecutionResult(action, success, self.mode, "simulation", 0.0)


Runner = Callable[..., subprocess.CompletedProcess[str]]


class AnsibleExecutor:
    mode = ExecutionMode.ANSIBLE

    def __init__(
        self,
        playbook_dir: Path,
        inventory: Path,
        timeout_seconds: int,
        ansible_bin: str = "ansible-playbook",
        runner: Runner = subprocess.run,
    ) -> None:
        self.playbook_dir = playbook_dir.resolve()
        self.inventory = inventory.resolve()
        self.timeout_seconds = timeout_seconds
        self.ansible_bin = ansible_bin
        self.runner = runner

    def command(self, action: RecommendedAction, request_id: str) -> list[str]:
        _validate(action, request_id)
        playbook = (self.playbook_dir / PLAYBOOKS[action]).resolve()
        if playbook.parent != self.playbook_dir:
            raise ActionNotAllowedError("chemin de playbook inattendu")
        return [
            self.ansible_bin,
            "-i",
            str(self.inventory),
            str(playbook),
            "-e",
            json.dumps({"request_id": request_id}),
        ]

    def execute(self, action: RecommendedAction, request_id: str) -> ExecutionResult:
        cmd = self.command(action, request_id)
        env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "ANSIBLE_CONFIG": str(self.playbook_dir / "ansible.cfg"),
            "ANSIBLE_LOCAL_TEMP": "/tmp/ansible-local",
            "ANSIBLE_NOCOLOR": "1",
        }
        start = time.monotonic()
        try:
            completed = self.runner(
                cmd,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(action, False, self.mode, "délai dépassé", time.monotonic() - start)
        duration = time.monotonic() - start
        tail = (completed.stdout or "")[-1500:] + (completed.stderr or "")[-1500:]
        logger.info(
            "executor.ansible_finished",
            extra={
                "event": "executor.ansible_finished",
                "action": action.value,
                "request_id": request_id,
                "returncode": completed.returncode,
                "duration_s": round(duration, 2),
                "output_tail": tail,
            },
        )
        detail = "ok" if completed.returncode == 0 else f"code retour {completed.returncode}"
        return ExecutionResult(action, completed.returncode == 0, self.mode, detail, duration)
