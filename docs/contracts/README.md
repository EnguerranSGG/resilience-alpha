# Contrats versionnés

Les schémas JSON de ce dossier sont **générés** depuis le paquet Python
`packages/resilience-contracts`. Ne les éditez pas à la main.

```bash
make contracts
```

| Fichier | Producteur | Consommateur | Notes |
|---|---|---|---|
| `anomaly-event.v1.schema.json` | `ml-detector` | `remediation` | `recommended_action` n'est **pas** une commande |
| `remediation-status.v1.schema.json` | `remediation` | frontend / Grafana | Vue publique |
| `remediation-incident.v1.schema.json` | `remediation` | frontend / dossier | Chronologie |

Toute rupture de compatibilité impose d'incrémenter `SCHEMA_VERSION` et de
coordonner P2 et P3 le même jour.
