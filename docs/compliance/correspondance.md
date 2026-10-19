# Correspondance exigences ↔ composants

| Attente de résilience | Composant du prototype | Preuve possible | Statut |
|---|---|---|---|
| Détection d'anomalie | Isolation Forest + Prometheus | événement + dashboard | SCAFFOLDED |
| Réponse automatisée encadrée | remediation + Ansible + NGINX | journal d'incidents | SCAFFOLDED (recette TODO) |
| Traçabilité | Loki, Alloy, journal JSONL | Explore Grafana | SCAFFOLDED |
| Moindre privilège | réseaux internes, no-new-privileges, pas de socket Docker | `compose.yml` + T11 | READY |
| Gestion des secrets | `./secrets` + SOPS documenté | absence dans Git (CI) | SCAFFOLDED |
| Tests | Pytest, Locust, smoke | CI + essais datés | partiel |
| Continuité | PCA/PRA S1 | procédure + Clip Chrono | TODO |

- [ ] TODO(P5) Ne conserver que les lignes pour lesquelles une preuve datée existe.
