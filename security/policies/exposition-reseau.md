# Politique d'exposition réseau

## Ports publiés sur le PC Hôte

| Service | Adresse par défaut | Démonstration | Justification |
|---|---|---|---|
| `gateway` (WAF + reverse proxy) | `127.0.0.1:8080` | `192.168.137.1:8080` (hotspot) | Seul point d'entrée applicatif, y compris pour le PC Attaquant |
| `grafana` | `127.0.0.1:3000` | inchangé | Écran du PC Hôte uniquement ; authentification obligatoire |
| `rag-assistant` (profil `rag`) | `127.0.0.1:8090` | inchangé | Usage opérateur local |
| `prometheus` (`compose.dev.yml` seulement) | `127.0.0.1:9090` | **non utilisé** | Collecte ML en développement |

Aucun autre service n'est publié : PostgreSQL, Loki, Alloy, Ollama, le moteur de remédiation, le détecteur ML et les API restent sur des réseaux Docker **internes**.

## Cloisonnement

| Réseau | Interne | Membres |
|---|---|---|
| `edge` | non | gateway |
| `apps` | oui | gateway (IP fixe), frontend, payment-api, auth-service, nginx-exporter |
| `control` | oui | gateway, remediation |
| `backend` | oui | payment-api, postgres |
| `observability` | oui | prometheus, loki, alloy, grafana, nginx-exporter, ml-detector, remediation, payment-api, auth-service |
| `admin` | non | grafana |
| `rag` | non | ollama, rag-assistant (téléchargement des modèles) |

## Règles de la passerelle

* Seules les routes métier sont relayées : `/api/payments*`, `/api/health/*`, `/auth/login`, et les vues **GET** `/api/remediation/status|incidents`. Tout autre `/api/*` → 404 ; `/metrics` n'est jamais exposé.
* L'adresse client retenue est `$remote_addr` ; `X-Forwarded-For` et `X-Real-IP` sont **écrasés**. Les API ne font confiance qu'à l'adresse fixe de la passerelle (`--forwarded-allow-ips`).
* WAF ModSecurity + OWASP CRS en mode bloquant (paranoïa 1, seuil d'anomalie 5).

## Interdits

* Publier Grafana, Prometheus, Loki ou Ollama sur l'interface du hotspot.
* Ajouter un port publié sans mise à jour de ce document et revue en PR.
* Monter le socket Docker dans un conteneur.
