# Definition of Done

Une tâche n'est **READY** que si tout ceci est vrai :

1. Code ou document dans le dépôt, sur une branche revue.
2. Tests du composant verts (ou raison de skip documentée, jamais un faux succès).
3. Pas de secret commité.
4. Statut READY / SCAFFOLDED / TODO mis à jour dans `PROJECT_STATUS.md` si le périmètre du composant change.
5. Un autre membre peut reproduire en suivant le README (pas « ça marche sur ma machine »).
6. Pour une preuve d'essai : date, versions, configuration, logs. Pas de CSV inventé.

## DoD spécifique Zero-Touch (jeudi)

- Attaque lancée depuis le PC Attaquant.
- Dégradation visible sur Grafana **sans** clic opérateur sur les conteneurs.
- Événement ML réel (modèle documenté).
- Mitigation automatique, nouvelle transaction `COMPLETED`, pas de doublon.
- Chronologie visible (UI + Grafana).
