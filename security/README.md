# security/

| Dossier | Contenu | Statut |
|---|---|---|
| [attack-tests/](attack-tests/README.md) | Test de charge contrôlé Locust + garde-fous | READY (outil), calibration TODO |
| [siem/](siem/README.md) | Règles Loki, requêtes SOC | SCAFFOLDED |
| [secrets/](secrets/README.md) | Gestion des secrets, partage SOPS/age | READY (local), SCAFFOLDED (SOPS) |
| [policies/](policies/README.md) | Exposition réseau, remédiation, règles d'équipe | SCAFFOLDED |

WAF : configuration dans [`infrastructure/waf`](../infrastructure/waf/README.md) et [`infrastructure/nginx`](../infrastructure/nginx).
