# Gestion des échecs

| Échec | État moteur | Action automatique | Action humaine (hors Zero-Touch) |
|---|---|---|---|
| Playbook `nginx -t` KO | `FAILED` | pas de profil partiel | logs passerelle, `make logs S=gateway` |
| Vérification métier KO | `FAILED` | retry après cooldown, puis escalade journalisée | `make gateway-restore` si besoin |
| Prometheus / Loki down | pas de mitigation (pas de corroboration) | OBSERVE | rétablir l'observabilité |
| Modèle absent | pas d'événement | silence | entraîner / monter le joblib |

Pendant la soutenance, si une intervention corrective humaine est nécessaire,
l'axe « remédiation autonome » du jury local est ND (0/5) d'après le sujet.
