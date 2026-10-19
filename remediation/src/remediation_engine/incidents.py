"""Registre des incidents et journal append-only (JSON Lines).

TODO(P2) : persister les incidents (PostgreSQL ou fichier versionné) pour
survivre à un redémarrage du moteur.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from resilience_contracts import ExecutionMode, IncidentView, RemediationState


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Incident:
    trigger_event_id: str
    execution_mode: ExecutionMode
    incident_id: str = field(default_factory=lambda: f"inc-{uuid.uuid4().hex[:12]}")
    opened_at: datetime = field(default_factory=_now)
    closed_at: datetime | None = None
    state: RemediationState = RemediationState.SUSPECT
    action: str | None = None
    attempts: int = 0
    verification_passed: bool | None = None
    first_anomaly_at: datetime | None = None
    recovered_at: datetime | None = None
    last_anomaly_at: datetime = field(default_factory=_now)
    last_attempt_at: datetime | None = None
    timeline: list[dict[str, str]] = field(default_factory=list)

    def view(self) -> IncidentView:
        return IncidentView(
            incident_id=self.incident_id,
            opened_at=self.opened_at,
            closed_at=self.closed_at,
            state=self.state,
            trigger_event_id=self.trigger_event_id,
            action=self.action,
            execution_mode=self.execution_mode,
            verification_passed=self.verification_passed,
            timeline=self.timeline[-50:],
        )


class IncidentStore:
    def __init__(self, journal_file: Path | None = None, keep: int = 50) -> None:
        self.journal_file = journal_file
        self.keep = keep
        self._incidents: list[Incident] = []
        self._lock = threading.Lock()
        if journal_file:
            journal_file.parent.mkdir(parents=True, exist_ok=True)

    def open(self, incident: Incident) -> Incident:
        with self._lock:
            self._incidents.append(incident)
            del self._incidents[: -self.keep]
        return incident

    def record(self, incident: Incident, kind: str, message: str) -> None:
        entry = {"at": _now().isoformat(), "kind": kind, "message": message}
        with self._lock:
            incident.timeline.append(entry)
            if self.journal_file:
                with self.journal_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"incident_id": incident.incident_id, **entry}, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 20) -> list[Incident]:
        with self._lock:
            return list(reversed(self._incidents[-limit:]))
