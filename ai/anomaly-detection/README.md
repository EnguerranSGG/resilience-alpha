# Détecteur d'anomalies (Isolation Forest)

Responsable : **P3 — IA & Data**. Statut : pipeline **READY** (code et tests) ; modèle **TODO** : aucun modèle entraîné sur des données réelles de la plateforme n'existe à ce jour.

## Rôle

Toutes les 5 s, le service `ml-detector` :

1. lit cinq features dans Prometheus (règles `resilience:*`, fenêtre 30 s) ;
2. calcule un score Isolation Forest (négatif = atypique) ;
3. compte les fenêtres anormales consécutives ;
4. si la fenêtre est anormale, envoie un **événement versionné** (`resilience_contracts.AnomalyEvent` v1.0) au moteur de remédiation, authentifié par `X-Resilience-Token`.

Il **n'exécute aucune action** et n'a accès ni au socket Docker, ni à la passerelle, ni à Ansible. **Sans modèle, il n'émet aucun événement** (`ml_detector_model_loaded = 0`).

## Features

| Feature | Règle Prometheus | Signification |
|---|---|---|
| `request_rate` | `resilience:request_rate:30s` | req/s métier sur payment-api (hors `/metrics`, `/health/*`) |
| `latency_p95` | `resilience:latency_p95_ms:30s` | latence p95 en ms (0 sans trafic) |
| `error_rate` | `resilience:error_rate:30s` | part de 5xx |
| `cpu_usage` | `resilience:cpu_usage:30s` | CPU du processus payment-api (s/s) |
| `active_requests` | `resilience:active_requests` | requêtes en cours |

## Cycle de vie du modèle

```bash
# 1. Démarrer la stack avec Prometheus publié en local
make up-dev

# 2. Collecter une période NORMALE (trafic légitime réaliste, ≥ 30 min recommandé)
make ml-collect MINUTES=30 LABEL=0

# 3. (Facultatif) collecter une période d'attaque contrôlée, pour l'évaluation uniquement
make ml-collect MINUTES=10 LABEL=1

# 4. Entraîner (apprentissage sur les seules lignes normales, découpage chronologique 60/20/20)
make ml-train DATA="data/collected-....csv data/collected-....csv"
# → models/isolation_forest.joblib + models/isolation_forest.json (métadonnées, métriques)
```

Le détecteur recharge le modèle à chaud dès que le fichier change (volume `models/` monté en lecture seule).

Métriques produites par `train` : précision, rappel, F1, matrice de confusion, taux de faux positifs, quantiles d'entraînement — calculées **uniquement** si des lignes étiquetées sont disponibles. Elles doivent être reprises telles quelles dans le dossier, avec la provenance des données.

## Données synthétiques

`make ml-train-synthetic` entraîne un modèle sur des données **générées** (`synthetic.py`). Il sert aux tests et à la démonstration du pipeline, jamais de preuve :

* le modèle est marqué `trained_on_synthetic: true` dans ses métadonnées et dans chaque événement ;
* la politique de remédiation **refuse** d'agir sur un tel modèle (décision `OBSERVE`) ;
* le dashboard affiche « CHARGÉ (SYNTHÉTIQUE) ».

Observation du 2026-10-19 (stack locale) : un modèle synthétique classe le trafic réel **au repos** comme anormal (score ≈ −0,17). Il n'est donc pas représentatif de la plateforme, ce qui confirme qu'il faut entraîner sur des données collectées.

## Tests

```bash
cd ai/anomaly-detection && ../../.venv/bin/python -m pytest   # 13 tests, ~40 s
```

## TODO (P3)

- [ ] Collecter des périodes normales réalistes (mardi) et documenter leur provenance dans `data/README.md`.
- [ ] Entraîner, évaluer, ajuster `contamination` et le seuil ; consigner les métriques réelles.
- [ ] Mesurer le délai de détection (nombre de fenêtres) pendant l'essai réseau.
- [ ] Justifier le choix d'Isolation Forest dans le dossier (axe 1).
