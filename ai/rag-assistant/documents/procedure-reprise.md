# Procédure de reprise après une surcharge HTTP

> Indexée par l'assistant RAG. Les objectifs chiffrés (RTO/RPO) sont à fixer par l'équipe dans
> `docs/pca-pra/`.

## Étapes automatiques

1. **Confirmation** : le moteur reçoit au moins trois fenêtres anormales consécutives du détecteur ML
   et constate une dégradation (latence p95 ou taux d'erreur au-dessus des seuils) ou des événements
   de sécurité (réponses 429/403 de la passerelle).
2. **Mitigation** : exécution de `mitigate.yml`. La passerelle copie le profil `mitigation`
   prévalidé, exécute `nginx -t`, recharge NGINX et confirme par un fichier d'état.
3. **Vérification métier** : via la passerelle, avec le compte de sonde `probe` :
   santé de l'API, connexion, création d'une transaction de 0,01 EUR, rejeu de la même clé
   d'idempotence (aucun doublon attendu), consultation de la transaction.
4. **État RECOVERED** si toutes les étapes réussissent ; sinon `FAILED` et nouvelle tentative après
   un délai, dans la limite du nombre maximal de tentatives.
5. **Restauration** : après une période stable sans anomalie, exécution de `restore.yml` (profil
   `normal`), puis état `NORMAL` et clôture de l'incident.

## Critères de reprise

- Une nouvelle transaction fictive légitime réussit après l'incident.
- Aucune transaction n'est dupliquée.
- La chronologie de l'incident est consultable.
- Un simple redémarrage de conteneur n'est pas considéré comme une reprise.

## En cas d'échec

- Vérifier les journaux du moteur (`{service="remediation-engine"}`) et de la passerelle
  (`log_type="control"`).
- Causes possibles : passerelle injoignable, profil rejeté par `nginx -t`, compte de sonde invalide,
  base de données indisponible.
