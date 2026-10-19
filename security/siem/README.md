# SIEM léger (Loki + Grafana)

Statut : **SCAFFOLDED** — collecte et règles chargées et vérifiées dans la stack ; seuils non calibrés, aucune alerte routée vers un canal de notification.

## Chaîne de collecte

```
gateway (accès JSON, audit ModSecurity, contrôle des profils)
payment-api / auth-service / remediation (JSON applicatif, journal d'incidents)
        │  fichiers dans des volumes dédiés (aucun accès au socket Docker)
        ▼
Grafana Alloy (lecture seule) ──► Loki ──► Grafana (dashboard + Explore)
                                    └──► ruler : security/siem/loki-rules/rules.yml
```

Labels : `service` (`gateway`, `payment-api`, `auth-service`, `remediation-engine`), `log_type` (`access`, `audit`, `control`, `app`, `journal`), `level`.

## Données sensibles

* Journal d'audit ModSecurity limité aux parties `A`, `F`, `H`, `Z` : **ni en-têtes de requête ni corps** (donc ni jeton JWT ni mot de passe).
* Journaux d'accès NGINX : pas d'en-tête `Authorization`, pas de corps.
* Les services n'écrivent jamais de mot de passe ni de jeton ; les paiements sont fictifs.
* Rétention Loki : 7 jours (`infrastructure/loki/loki.yml`).

## Règles (`loki-rules/rules.yml`)

| Règle | Signal | Usage |
|---|---|---|
| `GatewayRateLimitBurst` | > 50 réponses 429 par IP en 1 min | Observer la limitation active |
| `WafBlockedRequests` | > 5 blocages 403 en 5 min | Tentatives d'injection |
| `AuthBruteForceSuspected` | > 10 échecs de connexion par IP en 5 min | Attaque d'identifiants |
| `RemediationEventUnauthorized` | événement refusé par le moteur | Intégrité de la chaîne de détection |

Ces règles **n'actionnent pas** la remédiation. La corroboration utilisée par le moteur est une requête Loki distincte (`remediation/src/remediation_engine/signals.py`).

Consultation : `./scripts/compose.sh exec grafana wget -qO- http://loki:3100/prometheus/api/v1/rules`, ou Grafana → Alerting → Alert rules (source Loki).

## Requêtes utiles (Grafana → Explore → Loki)

```logql
{service="gateway", log_type="access"} | json | status="429"
{service="gateway", log_type="audit"}
{service="remediation-engine"} |= "remediation.transition"
sum by (status) (count_over_time({service="gateway", log_type="access"} | json [1m]))
```

## TODO (P4)

* Calibrer les seuils après les essais réseau réels.
* Décider d'un canal de notification (Alertmanager ou contact point Grafana) — non configuré à ce jour.
* Rédiger la procédure SOC d'analyse d'un incident à partir de ces requêtes.
