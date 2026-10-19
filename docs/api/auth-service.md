# auth-service

Émission de JWT RS256 pour des comptes **fictifs** listés dans `secrets/auth_users` (non versionné).

## Routes

| Méthode | Chemin | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | non (limité à 2 r/s par IP) | Identifiants → JWT |
| GET | `/health/live` | non | Processus vivant |
| GET | `/health/ready` | non | Clé privée + utilisateurs chargés |
| GET | `/metrics` | *non relayé* | Prometheus |

Comptes générés par `scripts/generate-secrets.sh` : `demo` (UI), `probe` (vérification métier), `loadtest` (Locust). Mots de passe dans `./secrets`, jamais dans Git.

## TODO

- [ ] TODO(P1) Rotation des clés JWT et TTL adaptés à la démo (aujourd'hui 900 s).
