# Responsabilités

| Rôle | Pendant l'incident (démo) | Hors démo |
|---|---|---|
| P1 | Observer l'UI métier, préparer la transaction de contrôle | Tests idempotence |
| P2 | Ne **pas** toucher aux conteneurs pendant le live | Playbooks, Grafana |
| P3 | Ne **pas** relancer le détecteur à la main | Modèle, features |
| P4 | Lancer Locust depuis le PC Attaquant uniquement | Garde-fous, WAF |
| P5 | Chronométrer MTTD/MTTR, Clip Chrono | Dossier, pitch |

Décision d'interrompre une attaque qui sortirait du labo : n'importe quel membre, immédiat, coach informé.
