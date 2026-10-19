#!/usr/bin/env bash
# Préparation d'un clone neuf : .env, secrets, environnement Python de développement.
#   ./scripts/bootstrap.sh            # .env + secrets
#   ./scripts/bootstrap.sh --dev      # + .venv Python et dépendances frontend
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo ".env créé depuis .env.example (à relire)"
else
    echo ".env existant conservé"
fi

./scripts/generate-secrets.sh

if [[ "${1:-}" == "--dev" ]]; then
    PY="$(command -v python3.12 || command -v python3)"
    "$PY" -m venv .venv
    .venv/bin/pip install --upgrade pip >/dev/null
    .venv/bin/pip install -r requirements-dev.txt
    (cd apps/frontend && npm ci --no-audit --no-fund)
    echo "Environnement de développement prêt (.venv, apps/frontend/node_modules)"
fi

echo
echo "Étape suivante : make up   (ou docker compose --env-file .env -f infrastructure/docker/compose.yml up -d --build)"
