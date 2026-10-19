#!/usr/bin/env bash
# Lancement MANUEL du test de charge contrôlé, depuis le PC Attaquant du laboratoire.
#
#   cp loadtest.env.example loadtest.env   # puis renseigner la cible autorisée
#   ./run-loadtest.sh                        # demande une confirmation explicite
#
# Arrêt immédiat : Ctrl+C. Les résultats CSV sont écrits dans results/<horodatage>/.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

ENV_FILE="${LOADTEST_ENV_FILE:-$HERE/loadtest.env}"
[[ -f "$ENV_FILE" ]] || { echo "Fichier $ENV_FILE absent (copier loadtest.env.example)" >&2; exit 2; }
set -a; source "$ENV_FILE"; set +a

PY="${PYTHON:-python3}"
"$PY" guardrails.py >/dev/null || exit 2
echo "Configuration validée : $("$PY" guardrails.py)"
echo
echo "Ce test envoie du trafic réel vers ${LOADTEST_TARGET}."
echo "Il ne doit viser QUE la plateforme du laboratoire (hotspot RESILIENCE-G<n>)."
read -r -p "Tapez exactement « LAB-ONLY » pour confirmer : " answer
[[ "$answer" == "LAB-ONLY" ]] || { echo "Annulé."; exit 1; }

OUT="results/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
cp "$ENV_FILE" "$OUT/loadtest.env.used"
sed -i.bak '/PASSWORD/d' "$OUT/loadtest.env.used" && rm -f "$OUT/loadtest.env.used.bak"

exec "$PY" -m locust -f locustfile.py --headless \
    --host "$LOADTEST_TARGET" \
    --users "$LOADTEST_USERS" \
    --spawn-rate "$LOADTEST_SPAWN_RATE" \
    --run-time "${LOADTEST_RUN_TIME_SECONDS}s" \
    --stop-timeout 5 \
    --csv "$OUT/locust" --csv-full-history \
    --only-summary
