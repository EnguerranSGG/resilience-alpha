# Objectifs RTO / RPO

Valeurs **cibles de démonstration**, à confronter aux mesures de jeudi. Ne pas
les présenter comme des engagements contractuels.

| Processus | RTO cible (hypothèse) | RPO cible (hypothèse) | Base technique | Mesure réelle |
|---|---|---|---|---|
| Prise de paiement fictive | 2 minutes après début d'anomalie persistante | 0 (pas de perte, idempotence) | mitigation NGINX + vérif métier | TODO |
| Supervision jury (Grafana) | 0 (reste local, non attaqué) | n/a | bind localhost | TODO |
| Assistant RAG | non critique | n/a | hors chemin | n/a |

MTTD / MTTR : extraire les horodatages du journal d'incidents et des métriques
Prometheus **après** un essai réel.

- [ ] TODO(P5/P2) Remplir la colonne « mesure réelle » jeudi, avec date et configuration.
