# Réseau de laboratoire (hotspot Windows)

Le sujet impose le point d'accès mobile Windows, souvent nommé `RESILIENCE-G<n>`,
avec une adresse de type `192.168.137.1` pour le PC Hôte. **Mesurer** plutôt que
supposer.

## PC Hôte (Windows + WSL2)

1. Activer le partage de connexion / hotspot (`Paramètres → Réseau → Point d'accès mobile`).
2. Noter SSID, bande, adresse IPv4 de l'interface hotspot (`ipconfig`).
3. Dans `.env` du dépôt (côté WSL, clone Linux recommandé, pas `/mnt/c`) :

   ```bash
   GATEWAY_BIND_ADDR=192.168.137.1   # remplacer par l'IP réellement observée
   GATEWAY_PORT=8080
   GRAFANA_BIND_ADDR=127.0.0.1
   ```

4. Pare-feu Windows : autoriser Docker / le port 8080 **uniquement** sur l'interface hotspot, pas sur le Wi-Fi campus.
5. Vérifier depuis le PC Hôte : `curl http://127.0.0.1:8080/healthz` puis `curl http://<ip-hotspot>:8080/healthz`.

## PC Attaquant

1. Se connecter au SSID du groupe uniquement.
2. Vérifier une IP dans le même /24 (`ipconfig` / `ip addr`).
3. `curl http://<ip-hote>:8080/healthz` doit répondre `ok`.
4. Configurer `security/attack-tests/loadtest.env` : `LOADTEST_TARGET` **et** `LOADTEST_AUTHORIZED_TARGETS` identiques, cette URL uniquement.
5. Ne jamais viser une IP campus, un autre groupe, ou une URL publique.

## Contrôles

- Grafana reste sur `127.0.0.1` : le jury le voit sur l'écran du PC Hôte.
- PostgreSQL, Prometheus, Loki, remédiation, Ollama : aucun port publié.
- Si `client_ip` dans Loki vaut l'IP NAT Docker, le documenter (risque résiduel).

## TODO

- [ ] TODO(P2) Tableau des IP réellement utilisées (lundi soir).
- [ ] TODO(P2) Paramètres WSL2 (`.wslconfig`) si RAM insuffisante.
