#!/usr/bin/env bash
# T10 — construit l'image de la passerelle et valide chaque profil NGINX avec `nginx -t`.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="resilience-alpha-gateway:validate"

docker build -q -t "$IMAGE" -f "$ROOT/infrastructure/nginx/Dockerfile" "$ROOT/infrastructure" >/dev/null
for profile in normal mitigation; do
    # L'entrypoint de l'image génère la configuration ModSecurity/CRS avant `nginx -t`.
    if docker run --rm --entrypoint sh "$IMAGE" -c \
        "cp /etc/nginx/profiles/$profile.conf /etc/nginx/active/profile.conf && exec /docker-entrypoint.sh nginx -t" \
        >/tmp/ra-nginx-$profile.log 2>&1; then
        echo "  [OK] profil $profile : nginx -t réussi"
    else
        echo "  [KO] profil $profile"; cat "/tmp/ra-nginx-$profile.log"; exit 1
    fi
done
