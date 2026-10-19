# WAF — ModSecurity v3 + OWASP CRS 4

Responsable : **P4 — Cybersécurité**. Statut : `SCAFFOLDED` (actif avec les réglages CRS par défaut,
exclusions et tests d'efficacité à réaliser).

## Où se trouve le WAF ?

Le WAF n'est pas un conteneur séparé : la passerelle `gateway` est construite à partir de l'image
officielle `owasp/modsecurity-crs:4.25.2-nginx-alpine-lts` (NGINX + libmodsecurity + CRS).
Un seul saut réseau, donc une seule adresse IP client à gérer.

```text
PC Attaquant / navigateur
        │  HTTP :8080 (seul port publié vers le réseau du hotspot)
        ▼
┌──────────────────────── gateway ────────────────────────┐
│ 1. limit_conn / limit_req (profil normal | mitigation) │
│ 2. ModSecurity + CRS (anomaly scoring, blocage ≥ 5)    │
│ 3. Routage : /api/payments, /api/health → payment-api  │
│              /auth/login → auth-service                │
│              /api/remediation/(status|incidents) GET   │
│              / → frontend                              │
└────────────────────────────────────────────────────────┘
```

## Réglages

| Variable (Dockerfile / compose) | Valeur | Effet |
|---|---|---|
| `BLOCKING_PARANOIA` | 1 | Niveau de paranoïa CRS bloquant |
| `ANOMALY_INBOUND` | 5 | Seuil de blocage des requêtes |
| `MODSEC_AUDIT_LOG` | `/var/log/gateway/modsec_audit.log` | Collecté par Alloy → Loki |
| `MODSEC_AUDIT_LOG_PARTS` | `AFHZ` | **Sans** en-têtes de requête ni corps : pas de JWT ni mot de passe dans les journaux |
| `MODSEC_AUDIT_LOG_RELEVANT_STATUS` | `^(?:5|403)` | Journalise les blocages WAF et les erreurs serveur |

## Vérifier que le WAF bloque

```bash
# Doit répondre 403 (règle CRS d'injection SQL) et produire une entrée dans modsec_audit.log
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/api/payments?id=1%27%20OR%20%271%27=%271"
```

## TODO

- [ ] TODO(P4) Tester les routes métier (login, paiement) pour repérer les faux positifs.
- [ ] TODO(P4) Décider d'un durcissement CRS dans le profil `mitigation` et le justifier.
- [ ] TODO(P4) Rotation du journal d'audit (volume limité en laboratoire).
