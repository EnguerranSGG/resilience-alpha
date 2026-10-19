# Diagrammes

## Architecture logique

```mermaid
flowchart LR
  subgraph lab [Laboratoire]
    Attacker[PC Attaquant]
    Host[PC Hôte / jury]
  end

  Attacker -->|HTTP GATEWAY_PORT| GW
  Host -->|HTTP GATEWAY_PORT| GW
  Host -->|localhost GRAFANA_PORT| Grafana

  subgraph edge [Réseau edge]
    GW[gateway NGINX + WAF]
  end

  subgraph apps [Réseau apps interne]
    FE[frontend]
    AUTH[auth-service]
    PAY[payment-api]
  end

  subgraph backend [Réseau backend interne]
    PG[(postgres)]
  end

  subgraph obs [Réseau observability interne]
    Prom[Prometheus]
    Loki[Loki]
    Alloy[Alloy]
    ML[ml-detector]
  end

  subgraph control [Réseau control interne]
    REM[remediation]
  end

  GW --> FE
  GW --> AUTH
  GW --> PAY
  GW -->|GET status/incidents| REM
  PAY --> PG
  Prom --> PAY
  Prom --> AUTH
  Prom --> REM
  Prom --> ML
  Alloy --> Loki
  ML -->|AnomalyEvent + jeton| REM
  REM -->|request.json| GW
```

## Séquence — attaque contrôlée et reprise

```mermaid
sequenceDiagram
  actor Att as PC Attaquant
  participant GW as gateway
  participant API as payment-api
  participant Prom as Prometheus
  participant ML as ml-detector
  participant REM as remediation
  actor User as Client légitime

  User->>GW: POST /api/payments (OK)
  Att->>GW: charge HTTP Locust (LAB-ONLY)
  GW->>API: trafic excessif
  API-->>Prom: latence / 5xx / requêtes actives
  ML->>Prom: scrape des features
  ML->>ML: Isolation Forest
  ML->>REM: AnomalyEvent (DOS_SUSPECTED)
  REM->>Prom: corroboration dégradation
  REM->>GW: playbook mitigate.yml (profil mitigation)
  GW->>GW: nginx -t puis reload
  Att->>GW: 429 rate-limited
  User->>GW: POST /api/payments (contrôle)
  REM->>User: vérification métier via gateway
  Note over REM: RECOVERED seulement si la transaction réussit
```

## TODO

- [ ] TODO(P2) Ajouter les volumes de contrôle (`gateway-requests` / `gateway-status`) sur un schéma de détail.
- [ ] TODO(P5) Version « grand public » pour le pitch de 5 minutes.
