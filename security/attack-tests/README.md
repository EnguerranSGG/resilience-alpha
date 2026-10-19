# Test de charge contrôlé (scénario DoS de laboratoire)

> **Usage exclusif sur les machines du laboratoire du groupe** (PC Hôte et PC Attaquant reliés par le hotspot `RESILIENCE-G<n>`). Aucune autre cible n'est autorisée.

Statut : **READY (outil)** — garde-fous testés unitairement et vérifiés en conditions réelles contre une instance locale. La **calibration** du scénario reste **TODO** (voir plus bas).

## Principe

Locust simule des clients authentifiés (compte dédié `loadtest`) qui créent des paiements **fictifs** à débit constant, plus quelques contrôles `/api/health/ready`. Le flux passe par la passerelle, exactement comme un utilisateur légitime : c'est un **DoS applicatif HTTP volumétrique contrôlé**, sans exploitation de vulnérabilité, sans falsification d'adresse, sans distribution.

## Garde-fous (`guardrails.py`)

| Règle | Mise en œuvre |
|---|---|
| Aucun lancement automatique | Uniquement via `run-loadtest.sh`, qui exige de taper `LAB-ONLY` ; aucun service Compose, aucune CI ne l'exécute |
| Cible explicitement autorisée | `LOADTEST_TARGET` doit figurer dans `LOADTEST_AUTHORIZED_TARGETS` ; aucune valeur par défaut |
| Pas de cible publique | Adresse IP privée ou de bouclage uniquement ; noms DNS, adresses publiques, multicast, `0.0.0.0` refusés |
| Durée maximale | `LOADTEST_RUN_TIME_SECONDS` obligatoire, ≤ 300 s, imposée à Locust (`--run-time`) |
| Utilisateurs limités | ≤ 50 ; montée ≤ 10/s |
| Débit prudent | ≤ 10 req/s par utilisateur et ≤ 300 req/s au total (`constant_throughput`) |
| Pas de contournement | Les options effectives de Locust (hôte, utilisateurs, durée) sont revérifiées à l'initialisation |
| Pas de distribution | Modes master/worker refusés |
| Transparence | `User-Agent` explicite, aucune falsification d'en-tête `X-Forwarded-For` |
| Arrêt immédiat | `Ctrl+C` (arrêt en ≤ 5 s, `--stop-timeout 5`) |

Tests : `python -m pytest security/attack-tests/tests` (26 cas).

## Utilisation (PC Attaquant)

```bash
cd security/attack-tests
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp loadtest.env.example loadtest.env      # renseigner la cible : http://192.168.137.1:8080
# déposer le mot de passe du compte loadtest (transmis via SOPS) dans le fichier indiqué
PYTHON=.venv/bin/python ./run-loadtest.sh
```

Résultats : `results/<horodatage>/locust_stats.csv`, `locust_stats_history.csv`, `locust_failures.csv` (non commités ; à archiver comme preuve **uniquement** pour un essai réellement effectué, avec date, versions et conditions).

## Observations de développement (non probantes)

Essais réalisés le 2026-10-19 sur un MacBook (Docker Desktop, cible `127.0.0.1`), stack par défaut, **aucun modèle ML chargé**. Ils servent à orienter la calibration, pas de preuve de recette.

| Configuration | Débit observé | p95 payment-api | 5xx | 429 passerelle |
|---|---|---|---|---|
| 20 utilisateurs × 5 req/s, 45 s | ~95 req/s | ~96 ms | 0 % | 0 % |
| 50 utilisateurs × 6 req/s, 45 s | ~236 req/s | ~199 ms | 0 % | ~20 % (profil **normal**) |

Conséquence : avec les réglages par défaut, la limite par IP du profil **normal** (200 r/s) bride l'attaque avant que le backend ne se dégrade. À calibrer par P2/P4 (mardi) : relever la limite du profil normal (`infrastructure/nginx/normal.conf`) et/ou ajuster `PAYMENT_PROCESSING_DELAY_MS` / `PAYMENT_DB_POOL_SIZE`, puis mesurer sur le matériel réel de la soutenance.

## Limite connue

Sous Docker Desktop (Windows/macOS), la passerelle peut voir l'adresse NAT de Docker au lieu de celle du PC Attaquant : la limitation par IP s'applique alors à tous les clients externes. Vérifier `client_ip` dans les journaux d'accès lors de l'essai réseau (voir `docs/procedures/reseau-laboratoire.md`).
