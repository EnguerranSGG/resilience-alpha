# Moteur de remédiation

API interne. Aucune route n'exécute une commande libre.

| Méthode | Chemin | Exposition | Description |
|---|---|---|---|
| POST | `/events` | réseau `observability` + jeton `X-Resilience-Token` | Ingestion `AnomalyEvent` |
| GET | `/public/status` | passerelle `/api/remediation/status` | État (NORMAL, SUSPECT, …) |
| GET | `/public/incidents` | passerelle `/api/remediation/incidents` | Chronologie |
| GET | `/health/live` | interne | |
| GET | `/health/ready` | interne | Jeton, probe, playbooks |
| GET | `/metrics` | Prometheus | État, mode simulation |

`POST /events` n'est **jamais** relayé par NGINX.

Mode d'exécution : `REMEDIATION_EXECUTION_MODE=ansible` (réel) ou `simulated` (aucune modification, journalisé `SIMULATION`).
