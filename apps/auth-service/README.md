# auth-service — authentification des comptes fictifs

Responsable : **P1 — Développement** (revue sécurité : **P4**). Statut : `READY` (socle minimal).

## Routes

| Méthode | Route | Description |
|---|---|---|
| POST | `/auth/login` | `{"username", "password"}` → `{"access_token", "token_type", "expires_in"}` |
| GET | `/health/live` | Processus vivant |
| GET | `/health/ready` | Clé privée chargée et au moins un compte défini |
| GET | `/metrics` | Métriques Prometheus (réseau interne uniquement) |

## Choix de sécurité

- JWT **RS256** : seul `auth-service` détient la clé privée ; `payment-api` ne reçoit que la clé publique.
- Durée de vie courte (`AUTH_TOKEN_TTL_SECONDS`, 15 min par défaut), claims `iss`, `aud`, `exp`, `nbf`, `jti`.
- Comptes fictifs chargés depuis le secret `auth_users` (généré par `scripts/generate-secrets.sh`),
  hachés en scrypt au démarrage. Aucun compte ni mot de passe n'existe dans le code ou dans Git.
- Comptes générés : `demo` (démonstration jury), `probe` (vérification post-remédiation),
  `loadtest` (test de charge depuis le PC Attaquant).
- Délai constant approximatif pour les comptes inexistants (pas d'énumération par le temps).
- Le rate limiting de `/auth/login` est appliqué par la passerelle NGINX.

## TODO

- [ ] TODO(P1) Révocation / rotation des jetons (liste `jti`) si nécessaire.
- [ ] TODO(P4) Alerte SIEM sur rafale de `auth.login_failed` (règle Loki préparée dans `security/siem/`).
