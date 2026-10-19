"""Fixtures partagées des tests d'acceptation (racine ``tests/``)."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = REPO_ROOT / "infrastructure" / "docker" / "compose.yml"


def compose_cmd(*args: str) -> list[str]:
    env_file = REPO_ROOT / ".env"
    command = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    if env_file.is_file():
        command[2:2] = ["--env-file", str(env_file)]
    command.extend(args)
    return command


def run_command(command: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def stack_is_running() -> bool:
    if os.environ.get("RESILIENCE_SKIP_LIVE") == "1":
        return False
    try:
        result = run_command(compose_cmd("ps", "--status", "running", "-q"), timeout=15)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def run() -> Callable[..., subprocess.CompletedProcess[str]]:
    return run_command


@pytest.fixture(scope="module")
def require_live_stack() -> None:
    if not stack_is_running():
        pytest.skip("Stack Docker inactive : lancer `make up` pour exécuter les tests live")


@pytest.fixture(scope="session")
def compose_exec() -> Callable[..., str]:
    def _exec(service: str, *args: str, timeout: int = 30) -> str:
        result = run_command(compose_cmd("exec", "-T", service, *args), timeout=timeout)
        if result.returncode != 0:
            pytest.fail(f"{service} {' '.join(args)} : {result.stderr or result.stdout}")
        return result.stdout

    return _exec
