#!/usr/bin/env bash
# Détection simple de secrets évidents dans les fichiers suivis par Git.
# Complément de gitleaks (exécuté en CI) ; utilisable sans outil supplémentaire.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Pas un dépôt Git" >&2; exit 2
fi

status=0
tracked="$(git ls-files)"

if echo "$tracked" | grep -E '^secrets/[^.]|\.pem$|\.key$|(^|/)\.env$' | grep -v -E '^secrets/README\.md$|\.example$'; then
    echo "ERREUR : fichiers sensibles suivis par Git (ci-dessus)"; status=1
fi

patterns=(
    '-----BEGIN [A-Z ]*PRIVATE KEY-----'
    'AKIA[0-9A-Z]{16}'
    'ghp_[A-Za-z0-9]{36}'
    'xox[baprs]-[A-Za-z0-9-]{10,}'
    'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
    'AGE-SECRET-KEY-1[0-9A-Z]{58}'
)
for pattern in "${patterns[@]}"; do
    if matches="$(git grep -n -I -E -e "$pattern" -- ':!scripts/check-secrets.sh' 2>/dev/null)"; then
        echo "ERREUR : motif sensible « $pattern » :"; echo "$matches"; status=1
    fi
done

if (( status == 0 )); then echo "Aucun secret évident détecté dans les fichiers suivis."; fi
exit "$status"
