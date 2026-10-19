# Gestion des secrets

Statut : **READY** pour la génération locale et l'injection par Docker secrets ; **SCAFFOLDED** pour le partage chiffré SOPS/age (procédure fournie, aucune clé d'équipe créée).

## Principes

1. Aucun secret dans Git, dans `.env`, dans les images ou dans les variables d'environnement : uniquement des **fichiers** montés en Docker secrets (`/run/secrets/*`) et lus par `*_FILE`.
2. Secrets générés localement (`scripts/generate-secrets.sh`), aléatoires, propres à chaque poste.
3. Clé privée JWT détenue par `auth-service` seul ; `payment-api` ne reçoit que la clé publique.
4. Jeton `remediation_event_token` partagé uniquement entre `ml-detector` et `remediation`.
5. Scans : `scripts/check-secrets.sh` (local) et gitleaks (CI).

## Partage dans l'équipe avec SOPS + age

Nécessaire seulement si plusieurs postes doivent partager **les mêmes** secrets (par exemple, le mot de passe du compte `loadtest` sur le PC Attaquant).

```bash
# 1. Chaque membre génère sa clé (une fois) et communique sa clé PUBLIQUE (age1...)
age-keygen -o ~/.config/sops/age/keys.txt

# 2. Le référent sécurité copie sops.example.yaml en .sops.yaml à la racine
#    et y remplace les destinataires par les clés publiques réelles de l'équipe.

# 3. Chiffrement du paquet de secrets (le fichier chiffré peut être commité)
./security/secrets/sops-pack.sh          # → security/secrets/lab-secrets.enc.yaml

# 4. Sur un autre poste membre de l'équipe
./security/secrets/sops-unpack.sh        # → ./secrets/*
```

Les clés privées age (`keys.txt`, `AGE-SECRET-KEY-…`) ne doivent **jamais** être commitées (`.gitignore` + scan).

## Vault

Non retenu pour le prototype : un serveur Vault ajouterait un service d'administration à exposer et à sécuriser pendant 4 jours. Justification à reprendre dans le dossier (axe 3, coût/bénéfice).

## Rotation

* Locale : `./scripts/generate-secrets.sh --force` puis `make reset` (la base conserve sinon l'ancien mot de passe) et `make up`.
* Après une démonstration publique : régénérer systématiquement.
