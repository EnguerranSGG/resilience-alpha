# secrets/

Répertoire **local** des secrets montés en Docker secrets. Son contenu (hors ce README) est ignoré par Git.

Génération : `./scripts/generate-secrets.sh` (ou `make secrets`).

| Fichier | Utilisé par |
|---|---|
| `postgres_password` | postgres, payment-api |
| `jwt_private_key.pem` | auth-service uniquement (signature RS256) |
| `jwt_public_key.pem` | payment-api (vérification) |
| `auth_users` | auth-service (`utilisateur:motdepasse:rôles`, comptes `demo`, `probe`, `loadtest`) |
| `probe_password` | remediation (vérification métier après remédiation) |
| `remediation_event_token` | ml-detector → remediation (`X-Resilience-Token`) |
| `grafana_admin_password` | grafana |
| `demo_password`, `loadtest_password` | consultation opérateur, non montés |

Partage chiffré au sein de l'équipe : [security/secrets/README.md](../security/secrets/README.md).
