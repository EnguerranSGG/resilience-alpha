# Backlog initial

Priorité : P0 bloquant démo, P1 nécessaire jeudi, P2 confort. Jour cible = fin de journée.

| ID | Tâche | Resp. | Prio | Dépend | Acceptation | Jour |
|---|---|---|---|---|---|---|
| T-P1-01 | Health + paiement + idempotence via passerelle | P1 | P0 | secrets | `make smoke` vert | Lun |
| T-P1-02 | Frontend login / formulaire / liste / statut / incidents | P1 | P0 | API | parcours UI manuel | Lun |
| T-P1-03 | Compte `loadtest` utilisable depuis le PC Attaquant | P1 | P0 | P4 | Locust s'authentifie | Lun |
| T-P1-04 | Migrations Alembic à la place de `create_all` | P1 | P2 | — | schéma versionné | Mer |
| T-P2-01 | `make up` sur le PC Hôte Windows/WSL2 | P2 | P0 | Docker | T01–T06 live | Lun |
| T-P2-02 | Hotspot + `GATEWAY_BIND_ADDR` mesuré | P2 | P0 | P4 | curl depuis PC Attaquant | Lun |
| T-P2-03 | Dashboard Grafana : avant / pendant / après | P2 | P0 | métriques | 7 panneaux lisibles | Mar |
| T-P2-04 | Calibration profil `normal` vs charge | P2 | P0 | P4 | dégradation **mesurable** | Mar |
| T-P2-05 | Chaîne Ansible mitigate/restore observée | P2 | P0 | P3 événement | timeline RECOVERED | Mer |
| T-P3-01 | Collecte Prometheus réelle (30+ min normal, 5 min charge) | P3 | P0 | P2 `up-dev` | CSV horodaté hors Git | Mar |
| T-P3-02 | Entraînement Isolation Forest **non synthétique** | P3 | P0 | T-P3-01 | `trained_on_synthetic=false` | Mar |
| T-P3-03 | Événement émis vers remédiation | P3 | P0 | modèle + jeton | Loki + `/incidents` | Mer |
| T-P3-04 | RAG indépendant (si RAM) | P3 | P2 | docs | `make rag-up` | Mer |
| T-P4-01 | Locust calibré, cible privée uniquement | P4 | P0 | P1 routes | 1 essai labo daté | Mar |
| T-P4-02 | WAF : faux positifs login/paiement | P4 | P1 | passerelle | login + paiement 200 | Mar |
| T-P4-03 | SOPS : partage secrets d'équipe | P4 | P1 | age | 5 postes déchiffrent | Mar |
| T-P4-04 | `client_ip` réel vs NAT Docker | P4 | P1 | hotspot | note dans risques résiduels | Mar |
| T-P5-01 | Noms, `G<n>`, EBIOS amorcé validé coachs | P5 | P0 | équipe | atelier lundi | Lun |
| T-P5-02 | Correspondance NIS2/DORA ↔ preuves | P5 | P1 | P2/P3 | 3 preuves datées | Mer |
| T-P5-03 | Recette S1 + MTTD/MTTR | P5 | P0 | chaîne | grille cochée | Jeu |
| T-P5-04 | Dossier, PPTX, Clip, ZIP | P5 | P0 | gel 17h | fichiers nommés | Jeu |
