# Vérification du rétablissement

La reprise n'est acquise **que** si une transaction légitime réussit en passant
par la passerelle (même chemin qu'un utilisateur), sans doublon.

1. Compte `probe` : login + `POST /api/payments` via `http://gateway:8080`.
2. Health `/api/health/ready` = 200.
3. État moteur → `RECOVERED`.
4. Après `REMEDIATION_RESTORE_AFTER_SECONDS` de stabilité : playbook `restore.yml` (profil `normal`).

Un simple redémarrage de conteneur n'est pas une preuve.
