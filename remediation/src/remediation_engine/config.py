from __future__ import annotations

from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from resilience_contracts import ExecutionMode, RecommendedAction


def read_secret(value: str | None, file: Path | None) -> str | None:
    if value:
        return value
    if file and file.is_file():
        return file.read_text(encoding="utf-8").strip()
    return None


class PolicySettings(BaseSettings):
    """Politique de décision. Toutes les conditions sont documentées dans
    ``docs/architecture/remediation.md``."""

    model_config = SettingsConfigDict(env_prefix="REMEDIATION_POLICY_", extra="ignore")

    score_threshold: float = Field(default=-0.05, ge=-1, le=1)
    min_consecutive_windows: int = Field(default=3, ge=1, le=100)
    require_corroboration: bool = True
    latency_p95_ms_threshold: float = Field(default=800, gt=0)
    error_rate_threshold: float = Field(default=0.05, gt=0, le=1)
    security_events_threshold: int = Field(default=20, ge=1)
    accept_synthetic_model: bool = False
    allowed_actions: set[RecommendedAction] = {RecommendedAction.ENABLE_RATE_LIMIT}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REMEDIATION_", extra="ignore")

    service_name: str = "remediation-engine"
    log_level: str = "INFO"
    log_file: Path | None = None
    journal_file: Path | None = None

    execution_mode: ExecutionMode = ExecutionMode.SIMULATED
    event_token: str | None = None
    event_token_file: Path | None = None

    prometheus_url: str = "http://prometheus:9090"
    loki_url: str = "http://loki:3100"
    gateway_url: str = "http://gateway:8080"
    http_timeout_seconds: float = Field(default=3.0, gt=0, le=30)

    probe_username: str = "probe"
    probe_password: str | None = None
    probe_password_file: Path | None = None
    verification_attempts: int = Field(default=6, ge=1, le=30)
    verification_delay_seconds: float = Field(default=2.0, ge=0, le=30)

    ansible_playbook_bin: str = "ansible-playbook"
    ansible_playbook_dir: Path = Path("/opt/remediation/ansible")
    ansible_inventory: Path = Path("/opt/remediation/ansible/inventory/remediation.yml")
    ansible_timeout_seconds: int = Field(default=90, ge=5, le=600)
    gateway_status_file: Path | None = None

    suspect_timeout_seconds: float = Field(default=60, gt=0)
    restore_after_seconds: float = Field(default=120, gt=0)
    retry_cooldown_seconds: float = Field(default=30, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=10)
    tick_interval_seconds: float = Field(default=5, gt=0)

    @cached_property
    def event_token_value(self) -> str | None:
        return read_secret(self.event_token, self.event_token_file)

    @cached_property
    def probe_password_value(self) -> str | None:
        return read_secret(self.probe_password, self.probe_password_file)
