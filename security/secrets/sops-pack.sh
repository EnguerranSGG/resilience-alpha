#!/usr/bin/env bash
# Chiffre le contenu de ./secrets dans security/secrets/lab-secrets.enc.yaml (SOPS + age).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/security/secrets/lab-secrets.enc.yaml"
command -v sops >/dev/null || { echo "sops requis" >&2; exit 1; }
[[ -f "$ROOT/.sops.yaml" ]] || { echo ".sops.yaml absent (voir sops.example.yaml)" >&2; exit 1; }
grep -q REMPLACER_PAR "$ROOT/.sops.yaml" && { echo ".sops.yaml contient encore des marqueurs" >&2; exit 1; }

PLAIN="$(mktemp)"
trap 'rm -f "$PLAIN"' EXIT
python3 - "$ROOT/secrets" "$PLAIN" <<'PY'
import json, pathlib, sys
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
data = {p.name: p.read_text() for p in sorted(src.iterdir()) if p.is_file() and p.name != "README.md"}
dst.write_text(json.dumps(data, indent=2))
PY
(cd "$ROOT" && sops --encrypt --input-type json --output-type yaml \
    --filename-override security/secrets/lab-secrets.enc.yaml "$PLAIN" > "$OUT")
echo "écrit : $OUT"
