# Checklist d'intégration (avant mardi soir)

À cocher **ensemble**, pas chacun dans son coin.

## Socle

- [ ] `make up` sur le PC Hôte de démo
- [ ] `make smoke` vert
- [ ] Frontend : login demo, paiement, liste
- [ ] Grafana localhost : API up, trafic, latence (erreurs éventuellement à 0)

## Réseau

- [ ] Hotspot up, IP notée dans `docs/architecture/flux-reseau.md`
- [ ] PC Attaquant joint `/healthz`
- [ ] PostgreSQL / Prometheus / Loki / remédiation non joignables depuis le PC Attaquant

## Contrats

- [ ] Exemple `docs/contracts/examples/anomaly-event.v1.json` toujours valide
- [ ] `ml-detector` et `remediation` utilisent la même version `1.0`
- [ ] Frontend affiche `NORMAL` (ou `SIMULATION` si mode simulated — à éviter en démo)

## Données ML

- [ ] Au moins un CSV de collecte réelle
- [ ] Décision écrite : modèle réel vs dérogation synthétique (P5)

## Sécurité

- [ ] Locust refuse une cible hors liste
- [ ] WAF 403 sur l'injection de smoke-test
- [ ] Secrets absents de `git ls-files`

Si un item est rouge mardi 18h : arbitrage P5, pas de nouvelle feature.
