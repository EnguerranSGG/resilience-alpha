# Scénarios couverts

| ID | Scénario | Couvert par l'automatisation ? | Commentaire |
|---|---|---|---|
| S1 | Surcharge HTTP sur `POST /api/payments` | visé | Scénario de soutenance |
| S2 | Saturation du pool PostgreSQL | partiel | Symptôme de S1 |
| S3 | Arrêt complet du PC Hôte | non | Reprise manuelle `make up` |
| S4 | Compromission d'un conteneur | non | Hors Zero-Touch de ce prototype |
| S5 | Perte du volume `pgdata` | non | RPO : voir rto-rpo.md |

- [ ] TODO(P5) Faire valider le périmètre S1 par les coachs lundi.
