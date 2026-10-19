# Scénario stratégique retenu — DoS applicatif HTTP

Hypothèse : un client du réseau `192.168.137.0/24` (ou équivalent mesuré)
envoie un volume élevé de `POST /api/payments` authentifiés vers la passerelle.

| Étape | Élément | Preuve visée |
|---|---|---|
| 1 | Point d'entrée unique `gateway:8080` | T11 |
| 2 | Saturation (latence, pool DB, 5xx ou 429) | Grafana, Prometheus |
| 3 | Isolation Forest sur fenêtre de métriques | événement `DOS_SUSPECTED` |
| 4 | Politique de remédiation (score + persistance + corroboration) | journal d'incidents |
| 5 | Profil `mitigation` (rate limit strict) | `status.json` passerelle |
| 6 | Transaction légitime de contrôle | T03 après incident |

Ce scénario **n'est pas** une attaque applicative (injection, contournement d'auth).
Le WAF reste en défense en profondeur mais n'est pas le mécanisme de reprise.

- [ ] TODO(P4) Calibrer débit / utilisateurs pour obtenir une dégradation **mesurable** sans masquer le backend (voir `security/attack-tests/README.md`).
- [ ] TODO(P3) Remplacer le modèle synthétique par des métriques réelles avant de parler de détection.
