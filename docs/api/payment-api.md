# payment-api

Service FastAPI de paiement **fictif**. Persistance PostgreSQL, montants `Decimal`, JWT RS256 (clé publique).

## Routes

| Méthode | Chemin interne | Chemin passerelle | Auth | Description |
|---|---|---|---|---|
| GET | `/health/live` | `/api/health/live` | non | Processus vivant |
| GET | `/health/ready` | `/api/health/ready` | non | PostgreSQL + clé JWT |
| GET | `/metrics` | *non relayé* | non | Prometheus |
| POST | `/payments` | `/api/payments` | Bearer | Créer une transaction |
| GET | `/payments` | `/api/payments` | Bearer | Lister (utilisateur courant) |
| GET | `/payments/{id}` | `/api/payments/{id}` | Bearer | Consulter |

## Transaction

Champs : `id`, `user_id`, `amount`, `currency`, `status`, `created_at`, `idempotency_key`.

Statuts : `PENDING`, `COMPLETED`, `FAILED`.

Idempotence : en-tête `Idempotency-Key` obligatoire. Même clé + même corps → `200` et `Idempotent-Replayed: true`. Même clé + corps différent → `409`.

## TODO

- [ ] TODO(P1) Migrations Alembic (aujourd'hui `create_all` au démarrage).
