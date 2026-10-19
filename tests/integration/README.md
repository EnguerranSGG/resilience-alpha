# Tests d'acceptation T01–T12

| ID | Objectif | Où | Marqueur | Statut |
|---|---|---|---|---|
| T01 | PostgreSQL démarre | `test_live_stack.py` | `live` | prêt, exécuté seulement si `make up` |
| T02 | Healthchecks payment-api | `test_live_stack.py` | `live` | prêt |
| T03 | Transaction fictive enregistrée | unitaire `apps/payment-api` + live | `live` | prêt |
| T04 | Idempotence | unitaire + live | `live` | prêt |
| T05 | Prometheus scrape les métriques | `test_live_stack.py` | `live` | prêt |
| T06 | Loki reçoit des logs | `test_live_stack.py` | `live` | prêt |
| T07 | Modèle ML entraîné et chargé | `ai/anomaly-detection/tests` | unitaire | prêt (données **synthétiques**) |
| T08 | Événement ML conforme | `packages/resilience-contracts` | unitaire | prêt |
| T09 | Actions non autorisées refusées | `remediation/tests` | unitaire | prêt |
| T10 | NGINX validable | `test_t10_nginx.py` | statique + `live` (`nginx -t`) | prêt |
| T11 | Services sensibles non publiés | `test_t11_exposure.py` | statique | prêt |
| T12 | RAG indépendant du socle | `test_t12_rag_independence.py` + tests RAG | statique / unitaire | prêt |

```bash
# Toujours exécutable (pas de Docker)
.venv/bin/pytest tests/integration -m "not live"

# Stack démarrée
make up
.venv/bin/pytest tests/integration -m live
```
