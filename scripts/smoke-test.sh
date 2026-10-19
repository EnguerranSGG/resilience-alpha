#!/usr/bin/env bash
# Test de fumée du socle démarré : passe par la passerelle comme un utilisateur légitime.
#   ./scripts/smoke-test.sh [http://localhost:8080]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${1:-http://localhost:${GATEWAY_PORT:-8080}}"
PASSWORD_FILE="$ROOT/secrets/demo_password"
failures=0

check() {
    local label="$1" expected="$2" actual="$3"
    if [[ "$actual" == "$expected" ]]; then printf '  [OK] %-45s %s\n' "$label" "$actual"
    else printf '  [KO] %-45s attendu %s, obtenu %s\n' "$label" "$expected" "$actual"; failures=$((failures + 1)); fi
}

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

echo "Smoke test sur $BASE"
check "passerelle /healthz" 200 "$(code "$BASE/healthz")"
check "API /api/health/live" 200 "$(code "$BASE/api/health/live")"
check "API /api/health/ready" 200 "$(code "$BASE/api/health/ready")"
check "frontend /" 200 "$(code "$BASE/")"
check "métriques non exposées /api/metrics" 404 "$(code "$BASE/api/metrics")"
check "ingestion remédiation non exposée" 403 "$(code -X POST -H 'Content-Type: application/json' -d '{}' "$BASE/api/remediation/events")"
check "vue publique remédiation" 200 "$(code "$BASE/api/remediation/status")"
check "WAF bloque une injection SQL" 403 "$(code "$BASE/api/payments?id=1%27%20OR%20%271%27=%271")"

if [[ -f "$PASSWORD_FILE" ]]; then
    token="$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
        -d "{\"username\":\"demo\",\"password\":\"$(cat "$PASSWORD_FILE")\"}" \
        | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
    check "connexion du compte demo" "true" "$([[ -n "$token" ]] && echo true || echo false)"
    key="smoke-$(date +%s)-$RANDOM"
    body='{"amount":"1.00","currency":"EUR","description":"smoke-test"}'
    first="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/payments" -H "Authorization: Bearer $token" \
        -H 'Content-Type: application/json' -H "Idempotency-Key: $key" -d "$body")"
    second="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/payments" -H "Authorization: Bearer $token" \
        -H 'Content-Type: application/json' -H "Idempotency-Key: $key" -d "$body")"
    check "création d'une transaction fictive" 201 "$first"
    check "rejeu idempotent (pas de doublon)" 200 "$second"
else
    echo "  [--] secrets/demo_password absent : tests de transaction ignorés"
fi

echo
if (( failures == 0 )); then echo "Smoke test réussi"; else echo "$failures échec(s)"; exit 1; fi
