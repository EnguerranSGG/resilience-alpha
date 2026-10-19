from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from guardrails import (
    MAX_RUN_TIME_SECONDS,
    MAX_USERS,
    GuardrailError,
    check_runtime,
    load_config,
    normalize_target,
)

VALID = {
    "LOADTEST_TARGET": "http://192.168.137.1:8080",
    "LOADTEST_AUTHORIZED_TARGETS": "http://192.168.137.1:8080",
    "LOADTEST_USERS": "20",
    "LOADTEST_SPAWN_RATE": "5",
    "LOADTEST_RUN_TIME_SECONDS": "120",
    "LOADTEST_RPS_PER_USER": "5",
}


def env(**overrides: str) -> dict[str, str]:
    return {**VALID, **overrides}


def test_valid_lab_configuration() -> None:
    config = load_config(VALID)
    assert config.target == "http://192.168.137.1:8080"
    assert config.max_total_rps == 100


@pytest.mark.parametrize("missing", list(VALID))
def test_every_parameter_is_mandatory(missing: str) -> None:
    values = dict(VALID)
    del values[missing]
    with pytest.raises(GuardrailError, match=missing):
        load_config(values)


@pytest.mark.parametrize(
    "target",
    [
        "http://8.8.8.8:80",
        "http://example.com",
        "http://payments.example.org:8080",
        "http://0.0.0.0:8080",
        "http://224.0.0.1",
        "ftp://192.168.137.1",
        "http://user:pw@192.168.137.1:8080",
        "http://192.168.137.1:8080/api/payments",
    ],
)
def test_non_lab_targets_are_refused(target: str) -> None:
    with pytest.raises(GuardrailError):
        normalize_target(target)


def test_target_must_be_explicitly_authorized() -> None:
    with pytest.raises(GuardrailError, match="AUTHORIZED"):
        load_config(env(LOADTEST_AUTHORIZED_TARGETS="http://192.168.137.2:8080"))


def test_localhost_is_normalized() -> None:
    config = load_config(
        env(LOADTEST_TARGET="http://localhost:8080", LOADTEST_AUTHORIZED_TARGETS="http://127.0.0.1:8080")
    )
    assert config.target == "http://127.0.0.1:8080"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("LOADTEST_USERS", str(MAX_USERS + 1)),
        ("LOADTEST_USERS", "0"),
        ("LOADTEST_RUN_TIME_SECONDS", str(MAX_RUN_TIME_SECONDS + 1)),
        ("LOADTEST_SPAWN_RATE", "100"),
        ("LOADTEST_RPS_PER_USER", "50"),
        ("LOADTEST_RPS_PER_USER", "0"),
        ("LOADTEST_USERS", "beaucoup"),
    ],
)
def test_limits_are_enforced(name: str, value: str) -> None:
    with pytest.raises(GuardrailError):
        load_config(env(**{name: value}))


def test_total_throughput_is_capped() -> None:
    with pytest.raises(GuardrailError, match="débit"):
        load_config(env(LOADTEST_USERS="50", LOADTEST_RPS_PER_USER="7"))
    assert load_config(env(LOADTEST_USERS="50", LOADTEST_RPS_PER_USER="6")).max_total_rps == 300


def test_runtime_options_cannot_bypass_configuration() -> None:
    config = load_config(VALID)
    ok = {"host": "http://192.168.137.1:8080", "users": 20, "run_time": 120, "distributed": False}
    check_runtime(config, **ok)
    for override in (
        {"host": "http://192.168.137.99:8080"},
        {"users": 21},
        {"run_time": None},
        {"run_time": 121},
        {"distributed": True},
    ):
        with pytest.raises(GuardrailError):
            check_runtime(config, **{**ok, **override})
