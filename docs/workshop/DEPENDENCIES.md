# Dépendances réciproques

| Consommateur | A besoin de | Producteur | Échéance utile |
|---|---|---|---|
| P3 | Métriques HTTP stables, recording rules | P1 + P2 | lundi soir / mardi |
| P2 | Contrat `AnomalyEvent` v1 (déjà dans le dépôt) | P3 | lundi (ne pas casser le schéma) |
| P4 | Routes et comptes (`/auth/login`, `/api/payments`, user `loadtest`) | P1 | lundi |
| P3 | Scénario de charge reproductible + labels | P4 | mardi |
| P2 | Calibration : le profil `normal` ne doit pas masquer l'attaque | P4 | mardi |
| P5 | Preuves (captures, MTTD/MTTR, limites) | tous | mercredi–jeudi |
| Frontend incidents | `GET /api/remediation/status` | P2 | déjà câblé |
| RAG | Documents Markdown à jour | tous | mercredi |

Point bloquant unique de la démo : **P3 sans modèle réel** ⇒ pas d'événement ⇒ pas de Zero-Touch.
Plan B à décider explicitement (dérogation modèle synthétique documentée) : P2 + P5, pas un silence.
