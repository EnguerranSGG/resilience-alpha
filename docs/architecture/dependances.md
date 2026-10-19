# Dépendances entre composants

```text
P1 payment-api / auth / frontend / PostgreSQL
        │
        │  métriques /health /payments
        ▼
P2 Prometheus, Loki, Alloy, Grafana, NGINX, Ansible
        │
        │  features Prometheus          ▲ contrat AnomalyEvent
        ▼                               │
P3 Isolation Forest ────────────────────┘
        │
        │  événements structurés
        ▼
P2 moteur de remédiation ── playbooks ── gateway
        ▲
        │  scénario de charge, WAF, SIEM, secrets
P4 ─────┘
        │
        ▼
P5 EBIOS, PCA/PRA, NIS2/DORA, recette, livrables
```

Détail opérationnel : [workshop/DEPENDENCIES.md](../workshop/DEPENDENCIES.md).
