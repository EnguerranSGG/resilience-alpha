#!/usr/bin/env bash
# Déchiffre security/secrets/lab-secrets.enc.yaml vers ./secrets (fichiers 0644, répertoire 0700).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IN="$ROOT/security/secrets/lab-secrets.enc.yaml"
command -v sops >/dev/null || { echo "sops requis" >&2; exit 1; }
[[ -f "$IN" ]] || { echo "$IN absent" >&2; exit 1; }

umask 077
mkdir -p "$ROOT/secrets" && chmod 700 "$ROOT/secrets"
sops --decrypt --output-type json "$IN" | python3 -c '
import json, os, pathlib, sys
target = pathlib.Path(sys.argv[1])
for name, value in json.load(sys.stdin).items():
    if "/" in name or name.startswith("."):
        raise SystemExit(f"nom de secret refusé : {name}")
    path = target / name
    path.write_text(value)
    # Fichiers montés dans les conteneurs : 0644 ; copies de consultation opérateur : 0600.
    os.chmod(path, 0o600 if name in {"demo_password", "loadtest_password"} else 0o644)
    print(f"  restauré : secrets/{name}")
' "$ROOT/secrets"
