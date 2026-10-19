# Documentation d'API

Les services exposent OpenAPI (`/docs`) **en interne uniquement**. Depuis l'extérieur, seul le chemin passant par la passerelle est autorisé.

| Service | Préfixe passerelle | OpenAPI interne |
|---|---|---|
| [payment-api](payment-api.md) | `/api` | `payment-api:8000/docs` |
| [auth-service](auth-service.md) | `/auth` | `auth-service:8000/docs` |
| [remediation](remediation.md) | `/api/remediation` (GET public) | non publié |
| rag-assistant | `127.0.0.1:8090` (profil `rag`) | local uniquement |

Les métriques Prometheus (`/metrics`) et `POST /events` du moteur **ne sont pas** relayés par la passerelle.
