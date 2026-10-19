# PROJECT_STATUS — RESILIENCE-ALPHA

Date : 2026-10-19. Dépôt local initialisé. **Aucun push GitHub.**

Légende : **READY** = fonctionnel et testé ici ; **SCAFFOLDED** = contrat/structure, logique incomplète ou non calibrée ; **TODO** = pas encore réalisé.

## 1. Arborescence (essentielle)

```text
resilience-alpha/
├── .github/workflows/ci.yml
├── apps/{payment-api,auth-service,frontend}
├── packages/resilience-contracts
├── ai/{anomaly-detection,rag-assistant}
├── remediation/
├── infrastructure/{docker,ansible,nginx,waf,prometheus,grafana,loki,alloy}
├── security/{attack-tests,siem,secrets,policies}
├── tests/{integration,resilience}
├── docs/{architecture,api,contracts,ebios,pca-pra,compliance,procedures,workshop}
├── scripts/
├── Makefile .env.example README.md CONTRIBUTING.md PROJECT_STATUS.md
```

## 2. Composants READY

| Composant | Preuve |
|---|---|
| payment-api (santé, paiement, idempotence, métriques) | 18 tests unitaires + T01–T04 live |
| auth-service JWT RS256 | 10 tests unitaires + login smoke/live |
| frontend (login, paiement, liste, statut, incidents) | `npm run lint` + `tsc` + `vite build` |
| PostgreSQL via Compose | T01 live |
| Contrats Pydantic v1 | 9 tests + exemple JSON |
| Moteur de remédiation (décision, états, allow-list, simulation) | 55 tests unitaires |
| Isolation Forest pipeline (données **synthétiques**) | 13 tests (T07/T08) |
| RAG index/API **sans** Ollama (LLM factice) | 6 tests (T12 unitaire) |
| Garde-fous Locust | 26 tests |
| Compose : réseaux internes, ports | T11 statique + `compose config` |
| Profils NGINX | T10 statique + `nginx -t` live |
| CI GitHub Actions (fichiers) | workflow présent, pas encore exécuté sur GitHub |

## 3. Composants SCAFFOLDED

| Composant | Ce qui manque |
|---|---|
| Détecteur ML en conditions réelles | **Aucun modèle commité** ; le conteneur tourne mais n'émet rien sans joblib |
| Remédiation Ansible en démo | Mécanisme prêt ; recette attaque→reprise **non validée** aujourd'hui |
| WAF CRS | Image active, exclusions/calibration TODO |
| SIEM Loki | Collecte réelle (octets ingérés observés) ; règles non calibrées |
| Grafana | Dashboard provisionné ; panneaux ML/remédiation vides tant que pas d'événement |
| SOPS | Scripts d'exemple, pas encore de coffre d'équipe |
| RAG + Ollama | Profil `rag` ; non démarré dans cette session |
| EBIOS / PCA / NIS2-DORA | Canevas, pas d'analyse finalisée |
| Alembic | `create_all` au démarrage |

## 4. Tests exécutés dans cette session

| Suite | Résultat |
|---|---|
| resilience-contracts | 9 passed |
| payment-api | 18 passed |
| auth-service | 10 passed |
| remediation | 55 passed |
| anomaly-detection | 13 passed |
| rag-assistant | 6 passed |
| attack-tests guardrails | 26 passed |
| T07–T12 statiques | 18 passed |
| Recette Zero-Touch (`tests/resilience`) | 8 **skipped** (volontaire, non validée) |
| T01–T06 + T10 live (stack Docker locale macOS) | 6 passed |
| Ruff check/format | OK |
| Frontend lint + tsc + build | OK |
| `docker compose config` (+ profil rag) | OK |
| Ansible `--syntax-check` | OK (avec `ANSIBLE_LOCAL_TEMP`) |
| CI GitHub | **non exécutée** (pas de remote) |
| Clip Chrono / dossier PDF | non produits (livrables jeudi) |

Stack observée `docker compose ps` : postgres, payment-api, auth-service, frontend, gateway, prometheus, loki, alloy, grafana, ml-detector, remediation, nginx-exporter **Up**. RAG/Ollama **non** lancés.

## 5. Commandes de démarrage

```bash
cp .env.example .env
./scripts/generate-secrets.sh
make up
make smoke
```

Grafana : http://127.0.0.1:3000 — UI : http://127.0.0.1:8080 — compte `demo` : `cat secrets/demo_password`.

## 6. Dépendances et blocages

- Docker Desktop requis pour le socle ; Python 3.12 + Node 22 pour le dev.
- **Blocage démo Zero-Touch** : pas de modèle entraîné sur métriques réelles → pas d'événement ML.
- Calibration Locust vs `limit_req` du profil `normal` (risque de 429 avant saturation backend).
- NAT Docker Desktop : IP client unique possible.
- Windows/WSL2 **non testé dans cette session** (environnement macOS).
- Loki `/ready` répond 503 sur cette instance unique alors que scrape + ingestion fonctionnent (T06 s'appuie sur `up` + labels + octets reçus).

## 7. Tâches à distribuer

Voir [docs/workshop/TASKS.md](docs/workshop/TASKS.md).

## 8. Priorités du lundi

| Rôle | Priorité |
|---|---|
| P1 | `make smoke` + parcours UI + compte `loadtest` |
| P2 | `make up` PC Hôte, hotspot, IP dans `.env` |
| P3 | Plan de collecte (`make up-dev` + `ml-collect`), ne pas vendre le synthétique |
| P4 | Curl depuis PC Attaquant, Locust `LAB-ONLY` sur IP privée |
| P5 | Rôles, `G<n>`, EBIOS amorcé, validation coachs |

## 9. Intégration avant mardi soir

[docs/workshop/INTEGRATION_CHECKLIST.md](docs/workshop/INTEGRATION_CHECKLIST.md) — notamment : smoke, hotspot, contrat v1, décision écrite modèle réel vs dérogation synthétique.

## 10. État Git et publication

- Dépôt Git **local**, branche `main`, commit initial prévu avec ce squelette.
- `.env` et `./secrets/` sont gitignorés.
- **Pas de remote, pas de push.** Pour GitHub : créer le dépôt vide, `git remote add origin …`, `git push -u origin main` **après accord de l'équipe**.
