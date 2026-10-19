# Recette de résilience (chaîne complète)

Statut : **TODO**. Aucun de ces scénarios n'est validé. Les tests correspondants
sont explicitement sautés (`pytest.mark.skip`) pour ne pas être confondus avec
une preuve de Zero-Touch Recovery.

## Chaîne attendue (vendredi)

1. Attaque contrôlée depuis le PC Attaquant (`security/attack-tests/run-loadtest.sh`).
2. Dégradation mesurable (latence p95, taux 5xx ou saturation du pool).
3. Détection Isolation Forest sur **métriques Prometheus réelles** (pas un modèle synthétique, sauf décision documentée de dérogation).
4. Remédiation automatique : profil NGINX `mitigation`.
5. Nouvelle transaction fictive réussie via la passerelle.
6. Aucun doublon (clé d'idempotence).
7. Journalisation de l'incident (`/api/remediation/incidents` + Loki).
8. Mesure MTTD et MTTR (horodatages Prometheus / journal d'incidents).

## Conditions préalables

- [ ] TODO(P3) Jeu de métriques réelles collecté et modèle entraîné (`make ml-train DATA=...`).
- [ ] TODO(P2/P4) Calibration de charge : le profil `normal` ne doit pas masquer la dégradation.
- [ ] TODO(P2) `REMEDIATION_EXECUTION_MODE=ansible` et playbooks vérifiés sur le PC Hôte.
- [ ] TODO(P5) Protocole de mesure MTTD/MTTR et grille de recette.

Ne commitez pas de CSV de résultats comme s'ils prouvaient la reprise.
