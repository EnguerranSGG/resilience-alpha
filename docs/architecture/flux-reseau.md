# Flux réseau

Voir aussi [procedures/reseau-laboratoire.md](../procedures/reseau-laboratoire.md) et [security/policies/exposition-reseau.md](../../security/policies/exposition-reseau.md).

## Implantation matérielle (sujet EPSI)

- **PC Hôte** : Windows 10/11 + Docker Desktop / WSL2. Exécute toute la stack.
- **PC Attaquant** : second ordinateur, uniquement le client Locust.
- **Hotspot Windows** : nom suggéré `RESILIENCE-G<n>`, réseau typique `192.168.137.0/24`, PC Hôte souvent `192.168.137.1`. Ces adresses **ne sont pas garanties** : les mesurer le lundi (`ipconfig` / `ip addr`).
- **Délestage IA (facultatif)** : troisième machine pour Ollama si la RAM du PC Hôte est insuffisante.

## Publication des ports

| Service | Bind par défaut | Accessible depuis le hotspot ? |
|---|---|---|
| `gateway` | `GATEWAY_BIND_ADDR:GATEWAY_PORT` (`127.0.0.1:8080`) | Oui **si** bind = IP du hotspot |
| `grafana` | `127.0.0.1:3000` | Non (écran du PC Hôte) |
| `rag-assistant` | `127.0.0.1:8090` (profil `rag`) | Non |
| PostgreSQL, Prometheus, Loki, remédiation, Ollama | non publiés | Non |

Pour la démonstration : dans `.env`, `GATEWAY_BIND_ADDR=192.168.137.1` (ou l'IP réelle du hotspot). Ne jamais publier Grafana sur `0.0.0.0`.

## Confiance dans l'adresse IP client

La passerelle est le seul proxy. Elle **écrase** `X-Real-IP` et `X-Forwarded-For` avec `$remote_addr`. Les API n'acceptent comme proxy de confiance que `GATEWAY_APPS_IP` (`10.231.20.10`).

Sous Docker Desktop, le trafic du PC Attaquant peut apparaître avec l'IP NAT de Docker : la limitation par IP s'applique alors à tous les clients externes. À vérifier dans les journaux `client_ip` dès le premier essai réseau.

## TODO

- [ ] TODO(P2/P4) Relever les adresses réelles du lundi et les coller ici.
- [ ] TODO(P4) Vérifier `client_ip` observé depuis le PC Attaquant.
