# Contribuer à RESILIENCE-ALPHA

## Branches

- `main` : toujours démarrable (`make up`). Pas de WIP cassé.
- Features : `p1/paiement-idempotence`, `p2/grafana-panels`, `p3/collecte-reelle`, etc.
- Une PR = un sujet. P5 relit les changements transverses (contrats, README).

## Revue

1. CI verte (`.github/workflows/ci.yml`).
2. Au moins un relecteur d'un **autre** rôle.
3. Contrats : si Pydantic change, `make contracts` et revue P2+P3.
4. Aucun secret, aucun résultat d'essai inventé.

## Qualité locale

```bash
make lint
make test          # unitaires + T07–T12 statiques
make smoke         # stack déjà up
```

Python 3.12, Ruff (`ruff.toml`), TypeScript strict côté frontend.

## Documentation

Français pour les humains, identifiants techniques en anglais. Statuts : `READY`, `SCAFFOLDED`, `TODO`.

## Interdits

- Pousser `.env`, `./secrets`, clés PEM, `loadtest.env`.
- Lancer Locust depuis Compose, la CI, ou un `make up`.
- Exposer Prometheus / PostgreSQL / remédiation sur le hotspot.
- Présenter un modèle synthétique ou un exécuteur `simulated` comme preuve de reprise réelle.
