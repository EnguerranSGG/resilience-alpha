#!/usr/bin/env bash
# Interroge Prometheus depuis le réseau interne (Prometheus n'est pas publié par défaut).
#   ./scripts/promql.sh 'resilience:request_rate:30s'
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
query="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1")"
"$ROOT/scripts/compose.sh" exec -T grafana wget -qO- "http://prometheus:9090/api/v1/query?query=$query"
echo
