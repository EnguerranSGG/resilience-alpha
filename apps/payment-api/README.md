# payment-api — service de paiement fictif

Responsable : **P1 — Développement**. Statut : `READY` (socle), voir `PROJECT_STATUS.md`.

## Routes

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET | `/health/live` | non | Le processus répond |
| GET | `/health/ready` | non | Base joignable et clé publique JWT chargée |
| GET | `/metrics` | non (réseau interne uniquement) | Métriques Prometheus |
| POST | `/payments` | JWT + en-tête `Idempotency-Key` | Crée une transaction fictive |
| GET | `/payments` | JWT | Liste les transactions de l'utilisateur (`limit` ≤ 100) |
| GET | `/payments/{id}` | JWT | Consulte une transaction de l'utilisateur |

Via la passerelle, ces routes sont préfixées par `/api` (ex. `POST /api/payments`).
`/metrics` n'est **pas** exposé par la passerelle.

Contrat détaillé : [`docs/api/payment-api.md`](../../docs/api/payment-api.md).

## Règles métier

- Montants en `Decimal` (`NUMERIC(12,2)`), transmis en JSON sous forme de chaîne (`"12.50"`).
- Statuts : `PENDING` → `COMPLETED` ou `FAILED` (règle de démonstration : montant > `PAYMENT_MAX_AMOUNT`).
- Idempotence : unicité `(user_id, idempotency_key)`. Même clé + même contenu → `200` et transaction
  existante (`Idempotent-Replayed: true`). Même clé + contenu différent → `409`.
- Saturation du pool de connexions → `503` + `Retry-After` (comportement observé pendant le DoS).

## Variables d'environnement

Préfixe `PAYMENT_` (voir `app/core/config.py` et `.env.example`). Les secrets sont lus depuis des
fichiers (`PAYMENT_DB_PASSWORD_FILE`, `PAYMENT_JWT_PUBLIC_KEY_FILE`) montés par Docker secrets.

`PAYMENT_PROCESSING_DELAY_MS` est un **paramètre de laboratoire** qui simule un coût de traitement afin
que la dégradation soit observable sous une charge volontairement modérée.

## Développement local

```bash
cd apps/payment-api
pip install -r requirements-dev.txt
pytest
```

Les tests unitaires utilisent SQLite en mémoire et une paire de clés RSA éphémère. Les tests contre
PostgreSQL réel sont dans `tests/integration/` à la racine du dépôt.

## TODO

- [ ] TODO(P1) Migrations Alembic au lieu de `create_all`.
- [ ] TODO(P1) Réconciliation des transactions restées `PENDING` après un arrêt brutal.
- [ ] TODO(P1) Journal d'audit métier séparé des logs techniques.
