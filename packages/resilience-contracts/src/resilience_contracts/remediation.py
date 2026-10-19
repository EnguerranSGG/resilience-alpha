"""Vues publiques du moteur de remédiation (lecture seule, consommées par le frontend)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict


class RemediationState(StrEnum):
    NORMAL = "NORMAL"
    SUSPECT = "SUSPECT"
    MITIGATING = "MITIGATING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"


class ExecutionMode(StrEnum):
    SIMULATED = "simulated"
    ANSIBLE = "ansible"


class IncidentView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    opened_at: AwareDatetime
    closed_at: AwareDatetime | None = None
    state: RemediationState
    trigger_event_id: str
    action: str | None = None
    execution_mode: ExecutionMode
    verification_passed: bool | None = None
    timeline: list[dict[str, str]]


class RemediationStatusView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: RemediationState
    execution_mode: ExecutionMode
    active_profile: str
    last_transition_at: AwareDatetime
    current_incident_id: str | None = None
