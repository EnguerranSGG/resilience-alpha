"""Génère ``dashboards/resilience-overview.json`` (dashboard as code).

Usage : ``python infrastructure/grafana/build_dashboard.py`` puis commiter le JSON.
Le test ``tests/integration/test_static_config.py`` vérifie que le JSON est à jour.
"""

from __future__ import annotations

import json
from pathlib import Path

PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
OUT = Path(__file__).parent / "dashboards" / "resilience-overview.json"

_next_id = 0


def _id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


def target(expr: str, legend: str = "", ds: dict = PROM, ref: str = "A") -> dict:
    return {"datasource": ds, "expr": expr, "legendFormat": legend, "refId": ref}


def stat(
    title: str,
    targets: list[dict],
    pos: tuple[int, int, int, int],
    mappings: list[dict],
    description: str,
    text_mode: str = "value",
) -> dict:
    x, y, w, h = pos
    return {
        "id": _id(),
        "type": "stat",
        "title": title,
        "description": description,
        "datasource": targets[0]["datasource"],
        "targets": targets,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "textMode": text_mode,
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
        },
        "fieldConfig": {
            "defaults": {
                "mappings": mappings,
                "noValue": "NON ALIMENTÉ",
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [{"color": "blue", "value": None}]},
            },
            "overrides": [],
        },
    }


def value_map(mapping: dict[str, tuple[str, str]]) -> list[dict]:
    return [{"type": "value", "options": {k: {"text": t, "color": c} for k, (t, c) in mapping.items()}}]


def timeseries(
    title: str,
    targets: list[dict],
    pos: tuple[int, int, int, int],
    description: str,
    unit: str = "short",
    draw: str = "line",
) -> dict:
    x, y, w, h = pos
    return {
        "id": _id(),
        "type": "timeseries",
        "title": title,
        "description": description,
        "datasource": targets[0]["datasource"],
        "targets": targets,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "noValue": "NON ALIMENTÉ",
                "custom": {
                    "drawStyle": draw,
                    "lineWidth": 2,
                    "fillOpacity": 10,
                    "lineInterpolation": "stepAfter" if draw == "line" else "linear",
                    "spanNulls": False,
                },
            },
            "overrides": [],
        },
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
    }


def logs(title: str, expr: str, pos: tuple[int, int, int, int], description: str) -> dict:
    x, y, w, h = pos
    return {
        "id": _id(),
        "type": "logs",
        "title": title,
        "description": description,
        "datasource": LOKI,
        "targets": [target(expr, ds=LOKI)],
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {"showTime": True, "wrapLogMessage": True, "sortOrder": "Descending", "dedupStrategy": "none"},
    }


def row(title: str, y: int) -> dict:
    return {
        "id": _id(),
        "type": "row",
        "title": title,
        "collapsed": False,
        "gridPos": {"x": 0, "y": y, "w": 24, "h": 1},
        "panels": [],
    }


def build() -> dict:
    panels = [
        row("État courant", 0),
        stat(
            "API de paiement",
            [target('up{job="payment-api"}')],
            (0, 1, 4, 4),
            value_map({"1": ("UP", "green"), "0": ("DOWN", "red")}),
            "Scrape Prometheus de payment-api.",
        ),
        stat(
            "Base de données",
            [target("payment_database_up")],
            (4, 1, 4, 4),
            value_map({"1": ("OK", "green"), "0": ("KO", "red")}),
            "Résultat du dernier /health/ready. NON ALIMENTÉ tant qu'aucun contrôle n'a été appelé.",
        ),
        stat(
            "État remédiation",
            [target("remediation_state == 1", "{{state}}")],
            (8, 1, 4, 4),
            [],
            "État de la machine à états du moteur.",
            text_mode="name",
        ),
        stat(
            "Profil passerelle",
            [target("remediation_active_profile == 1", "{{profile}}")],
            (12, 1, 4, 4),
            [],
            "Dernier profil NGINX appliqué par le moteur (normal | mitigation).",
            text_mode="name",
        ),
        stat(
            "Exécuteur",
            [target("remediation_executor_simulated")],
            (16, 1, 4, 4),
            value_map({"1": ("SIMULATION", "orange"), "0": ("ANSIBLE", "green")}),
            "SIMULATION = aucune configuration réellement modifiée.",
        ),
        stat(
            "Modèle ML",
            [target("ml_detector_model_loaded + 2 * ml_detector_model_synthetic")],
            (20, 1, 4, 4),
            value_map(
                {"0": ("AUCUN MODÈLE", "red"), "1": ("CHARGÉ (réel)", "green"), "3": ("CHARGÉ (SYNTHÉTIQUE)", "orange")}
            ),
            "Sans modèle, le détecteur n'émet aucun événement.",
        ),
        row("Trafic et performance", 5),
        timeseries(
            "Trafic HTTP",
            [
                target("resilience:request_rate:30s", "payment-api (métier)"),
                target("resilience:gateway_request_rate:30s", "passerelle (toutes requêtes)", ref="B"),
            ],
            (0, 6, 12, 8),
            "Requêtes par seconde (fenêtre glissante 30 s).",
            unit="reqps",
        ),
        timeseries(
            "Latence p95",
            [target("resilience:latency_p95_ms:30s", "p95")],
            (12, 6, 12, 8),
            "Latence p95 des routes métier de payment-api.",
            unit="ms",
        ),
        timeseries(
            "Taux d'erreurs 5xx",
            [target("resilience:error_rate:30s", "5xx / total")],
            (0, 14, 12, 7),
            "Part des réponses 5xx de payment-api.",
            unit="percentunit",
        ),
        timeseries(
            "Requêtes actives et CPU",
            [
                target("resilience:active_requests", "requêtes actives"),
                target("resilience:cpu_usage:30s", "CPU (s/s)", ref="B"),
            ],
            (12, 14, 12, 7),
            "Saturation du service.",
        ),
        row("Sécurité, détection et remédiation", 21),
        timeseries(
            "Événements de sécurité (passerelle)",
            [
                target(
                    'sum by (status) (count_over_time({service="gateway", log_type="access"} | json | status=~"429|403" [30s]))',
                    "HTTP {{status}}",
                    ds=LOKI,
                )
            ],
            (0, 22, 8, 8),
            "429 = limitation NGINX, 403 = blocage WAF. Source : Loki.",
            draw="bars",
        ),
        timeseries(
            "Détection ML",
            [
                target("ml_detector_anomaly_score", "score Isolation Forest"),
                target("ml_detector_is_anomaly", "anomalie (0/1)", ref="B"),
                target("ml_detector_consecutive_anomalies", "fenêtres consécutives", ref="C"),
            ],
            (8, 22, 8, 8),
            "NON ALIMENTÉ tant qu'aucun modèle n'est chargé. Score négatif = atypique.",
        ),
        timeseries(
            "Chronologie de la remédiation",
            [target("remediation_state == 1", "{{state}}")],
            (16, 22, 8, 8),
            "État du moteur dans le temps (avant / pendant / après l'incident).",
        ),
        logs(
            "Journal du moteur de remédiation",
            '{service="remediation-engine", log_type="app"} |~ "remediation\\\\.|executor\\\\.|verification\\\\."',
            (0, 30, 12, 10),
            "Décisions, transitions, actions et vérifications.",
        ),
        logs(
            "WAF et contrôle passerelle",
            '{service="gateway", log_type=~"audit|control"}',
            (12, 30, 12, 10),
            "Blocages ModSecurity et changements de profil NGINX.",
        ),
    ]
    return {
        "uid": "resilience-overview",
        "title": "RESILIENCE-ALPHA — Vue incident",
        "tags": ["resilience-alpha"],
        "timezone": "browser",
        "refresh": "5s",
        "time": {"from": "now-15m", "to": "now"},
        "schemaVersion": 39,
        "version": 1,
        "editable": False,
        "panels": panels,
        "templating": {"list": []},
        "annotations": {"list": []},
    }


def render() -> str:
    global _next_id
    _next_id = 0
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"écrit : {OUT}")
