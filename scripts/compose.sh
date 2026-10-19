#!/usr/bin/env bash
# Raccourci vers docker compose avec le bon fichier et le .env racine.
#   ./scripts/compose.sh ps
#   ./scripts/compose.sh logs -f gateway
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec docker compose --project-directory "$ROOT/infrastructure/docker" --env-file "$ROOT/.env" \
    -f "$ROOT/infrastructure/docker/compose.yml" "$@"
