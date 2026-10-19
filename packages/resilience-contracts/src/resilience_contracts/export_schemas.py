"""Génère les schémas JSON publiés dans ``docs/contracts/``.

Usage : ``python -m resilience_contracts.export_schemas docs/contracts``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from resilience_contracts.events import AnomalyEvent
from resilience_contracts.remediation import IncidentView, RemediationStatusView

SCHEMAS = {
    "anomaly-event.v1.schema.json": AnomalyEvent,
    "remediation-status.v1.schema.json": RemediationStatusView,
    "remediation-incident.v1.schema.json": IncidentView,
}


def render(model: type) -> str:
    return json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    target = Path(argv[1] if len(argv) > 1 else "docs/contracts")
    target.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS.items():
        (target / filename).write_text(render(model), encoding="utf-8")
        print(f"écrit : {target / filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
