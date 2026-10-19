# RESILIENCE-ALPHA — commandes usuelles. `make help` pour la liste.
SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_FILE ?= infrastructure/docker/compose.yml
COMPOSE := docker compose --env-file .env -f $(COMPOSE_FILE)
COMPOSE_DEV := $(COMPOSE) -f infrastructure/docker/compose.dev.yml
VENV ?= .venv
PY := $(VENV)/bin/python
FRONTEND := apps/frontend

PYTEST_TARGETS := packages/resilience-contracts apps/payment-api apps/auth-service remediation \
                  ai/anomaly-detection ai/rag-assistant
PY_SOURCES := packages apps/payment-api apps/auth-service remediation ai infrastructure/grafana \
              security/attack-tests tests

.PHONY: help
help: ## Affiche cette aide
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- préparation
.PHONY: check-env bootstrap secrets install-dev
check-env: ## Vérifie les prérequis du poste
	@./scripts/check-environment.sh

bootstrap: ## Crée .env et les secrets locaux
	@./scripts/bootstrap.sh

secrets: ## Génère les secrets manquants dans ./secrets
	@./scripts/generate-secrets.sh

install-dev: ## Crée .venv et installe les dépendances de développement (Python + frontend)
	@./scripts/bootstrap.sh --dev

.env:
	@echo ".env absent : lancer 'make bootstrap'" && exit 1

# ------------------------------------------------------------------ cycle de vie
.PHONY: up up-dev down reset logs ps build config
up: .env ## Démarre le socle (sans RAG)
	$(COMPOSE) up -d --build --wait

up-dev: .env ## Démarre le socle + Prometheus publié sur 127.0.0.1:9090
	$(COMPOSE_DEV) up -d --build --wait

down: .env ## Arrête la stack (les volumes sont conservés)
	$(COMPOSE) --profile rag down

reset: .env ## Arrête la stack et SUPPRIME les volumes (base, logs, métriques)
	$(COMPOSE) --profile rag down -v

logs: .env ## Suit les journaux (make logs S=gateway pour un service)
	$(COMPOSE) logs -f --tail=100 $(S)

ps: .env ## État des conteneurs
	$(COMPOSE) ps

build: .env ## Construit les images
	$(COMPOSE) build

config: .env ## Valide la configuration Compose (T11 statique)
	$(COMPOSE) config --quiet && echo "compose.yml valide"
	$(COMPOSE) --profile rag config --quiet && echo "compose.yml (profil rag) valide"

# ---------------------------------------------------------------- qualité
.PHONY: test test-integration test-resilience lint format frontend-lint frontend-build contracts dashboard validate-nginx check-secrets
test: ## Tests unitaires de tous les composants (sans Docker)
	@set -e; for d in $(PYTEST_TARGETS); do echo "== $$d"; (cd $$d && $(abspath $(PY)) -m pytest); done
	$(PY) -m pytest security/attack-tests/tests
	$(PY) -m pytest tests/integration tests/resilience -m "not live"

test-integration: ## Tests d'acceptation live T01-T06/T10 (stack démarrée)
	$(PY) -m pytest tests/integration -m live

test-resilience: ## Scénarios de recette (charge contrôlée ; voir tests/resilience/README.md)
	$(PY) -m pytest tests/resilience -m resilience

lint: frontend-lint ## Ruff (Python) + ESLint/TypeScript (frontend)
	$(VENV)/bin/ruff check $(PY_SOURCES)
	$(VENV)/bin/ruff format --check $(PY_SOURCES)

format: ## Formate le code Python
	$(VENV)/bin/ruff check --fix $(PY_SOURCES)
	$(VENV)/bin/ruff format $(PY_SOURCES)

frontend-lint:
	cd $(FRONTEND) && npm run lint && npx tsc -b --noEmit

frontend-build: ## Build de production du frontend
	cd $(FRONTEND) && npm run build

contracts: ## Régénère les schémas JSON du contrat d'événement
	$(PY) -m resilience_contracts.export_schemas docs/contracts

dashboard: ## Régénère le dashboard Grafana
	$(PY) infrastructure/grafana/build_dashboard.py

validate-nginx: ## T10 : nginx -t sur chaque profil de la passerelle
	@./scripts/validate-nginx.sh

check-secrets: ## Recherche de secrets dans les fichiers suivis
	@./scripts/check-secrets.sh

.PHONY: ci
ci: lint test config ## Qualité locale alignée sur la CI (sans Docker live)

.PHONY: smoke gateway-restore
smoke: ## Smoke test via la passerelle (stack démarrée)
	@./scripts/smoke-test.sh

gateway-restore: .env ## Action opérateur : remet la passerelle sur le profil normal (via le playbook)
	$(COMPOSE) exec -w /opt/remediation/ansible remediation \
		ansible-playbook restore.yml -e request_id=operator-$$(date +%s)
	$(COMPOSE) restart remediation

# ---------------------------------------------------------------------- ML
.PHONY: ml-collect ml-train ml-train-synthetic
ml-collect: ## Collecte les features (stack lancée via up-dev ; make ml-collect MINUTES=30 LABEL=0)
	cd ai/anomaly-detection && PYTHONPATH=src $(abspath $(PY)) -m anomaly_detection.collect \
		--prometheus http://127.0.0.1:9090 --minutes $(or $(MINUTES),30) $(if $(LABEL),--label $(LABEL)) \
		--out data/collected-$$(date +%Y%m%d-%H%M%S).csv

ml-train: ## Entraîne sur des données collectées (make ml-train DATA=data/x.csv)
	@test -n "$(DATA)" || (echo "DATA=chemin/vers/fichier.csv requis" && exit 1)
	cd ai/anomaly-detection && PYTHONPATH=src $(abspath $(PY)) -m anomaly_detection.train --data $(DATA)

ml-train-synthetic: ## Entraîne un modèle de DÉMONSTRATION sur données synthétiques (marqué comme tel)
	cd ai/anomaly-detection && PYTHONPATH=src $(abspath $(PY)) -m anomaly_detection.train --synthetic

# ---------------------------------------------------------------------- RAG
.PHONY: rag-up rag-pull rag-index
rag-up: .env ## Démarre Ollama + l'assistant RAG (profil rag)
	$(COMPOSE) --profile rag up -d --build

rag-pull: .env ## Télécharge les modèles Ollama configurés
	$(COMPOSE) --profile rag exec ollama ollama pull $${RAG_CHAT_MODEL:-llama3.2:3b}
	$(COMPOSE) --profile rag exec ollama ollama pull $${RAG_EMBEDDING_MODEL:-nomic-embed-text}

rag-index: .env ## (Re)construit l'index documentaire
	$(COMPOSE) --profile rag exec rag-assistant python -m rag_assistant.index
