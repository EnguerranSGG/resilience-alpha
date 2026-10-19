# Ansible — playbooks de déploiement et de remédiation

Responsable : **P2 — Infrastructure**.

| Playbook | Exécuté par | Où | Effet | Statut |
|---|---|---|---|---|
| `deploy.yml` | opérateur | PC Hôte (WSL2/macOS/Linux) | vérifie `.env` et secrets, `docker compose up --wait`, attend la passerelle | `SCAFFOLDED` — exécuté avec succès sur macOS le 2026-10-19 ; non testé sous Windows/WSL2 |
| `mitigate.yml` | moteur de remédiation | conteneur `remediation` | demande le profil `mitigation`, attend `nginx -t` + reload | `READY` — exécuté par le moteur dans la stack locale le 2026-10-19 (déclenché par un événement de test injecté, voir `PROJECT_STATUS.md`) |
| `restore.yml` | moteur de remédiation, opérateur (`make gateway-restore`) | conteneur `remediation` | demande le profil `normal` | `READY` — même essai (restauration automatique après stabilité) |

## Modèle de sécurité de la remédiation

```text
remediation (uid 10001, sans capacités, sans socket Docker)
  └─ ansible-playbook mitigate.yml -e '{"request_id": "inc-…"}'
       └─ écrit request.json  ─▶ volume gateway-requests (rw pour remediation, ro pour gateway)
                                     │
gateway (uid nginx) ◀────────────────┘ profile-watcher.sh
  ├─ vérifie le nom de profil (liste blanche : normal | mitigation)
  ├─ copie /etc/nginx/profiles/<profil>.conf (image, lecture seule)
  ├─ nginx -t  → reload  (sinon restauration du profil précédent)
  └─ écrit status.json ─▶ volume gateway-status (rw pour gateway, ro pour remediation)
```

Conséquences :

- le moteur ne peut **que** choisir entre deux profils figés dans l'image ; il ne peut pas injecter de
  configuration NGINX ni exécuter de commande dans un autre conteneur ;
- aucun composant n'a accès au socket Docker (`/var/run/docker.sock`) ;
- le profil est fixé dans chaque playbook ; seul `request_id` (regex stricte) est transmis.

## Commandes utiles

```bash
# Vérification syntaxique (CI)
ansible-playbook -i infrastructure/ansible/inventory/remediation.yml --syntax-check infrastructure/ansible/mitigate.yml

# Déploiement depuis le PC Hôte (WSL2 : depuis le dépôt cloné dans le système de fichiers Linux)
ansible-playbook -i infrastructure/ansible/inventory/host.yml infrastructure/ansible/deploy.yml
```

## TODO

- [ ] TODO(P2) Tester `deploy.yml` sur le PC Hôte Windows/WSL2 de la démonstration.
- [ ] TODO(P2) Playbook optionnel de collecte de preuves (export logs/incidents) pour le dossier.
