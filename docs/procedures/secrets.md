# Secrets

Aucun secret n'est versionné. Génération locale :

```bash
./scripts/generate-secrets.sh
```

Fichiers dans `./secrets/` (répertoire 0700, ignoré par Git) :

| Fichier | Usage |
|---|---|
| `postgres_password` | PostgreSQL |
| `jwt_private_key.pem` / `jwt_public_key.pem` | RS256 |
| `auth_users` | `user:password:role` |
| `demo_password` / `loadtest_password` | lecture opérateur |
| `probe_password` | vérification métier |
| `remediation_event_token` | ingestion ML → remédiation |
| `grafana_admin_password` | Grafana local |

Partage d'équipe : [security/secrets/README.md](../../security/secrets/README.md) (SOPS + age).
Ne jamais coller un secret dans un chat d'IA cloud, un ticket GitHub ou le Clip Chrono.
