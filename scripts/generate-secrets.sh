#!/usr/bin/env bash
# Génère les secrets LOCAUX de développement/démonstration dans ./secrets (ignoré par Git).
#
#   ./scripts/generate-secrets.sh           # crée les secrets manquants, conserve les existants
#   ./scripts/generate-secrets.sh --force   # régénère tout (puis `make reset` : la base garde l'ancien mot de passe)
#
# Prérequis : bash, openssl (WSL2, Git Bash, macOS, Linux).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/secrets"
FORCE="${1:-}"

command -v openssl >/dev/null || { echo "openssl est requis" >&2; exit 1; }

umask 077
mkdir -p "$DIR"
chmod 700 "$DIR"

random() { openssl rand -base64 64 | tr -dc 'A-Za-z0-9' | cut -c1-"${1:-32}"; }

exists() { [[ -f "$DIR/$1" && "$FORCE" != "--force" ]]; }

# Les conteneurs lisent les secrets avec leur propre uid : fichiers 0644 dans un répertoire 0700.
publish() { chmod 644 "$DIR/$1"; echo "  généré  : secrets/$1"; }

write() {
    local name="$1" value="$2"
    if exists "$name"; then echo "  conservé: secrets/$name"; return; fi
    printf '%s' "$value" > "$DIR/$name"
    publish "$name"
}

echo "Secrets locaux dans $DIR"
write postgres_password "$(random 32)"
write remediation_event_token "$(random 48)"
write grafana_admin_password "$(random 24)"

if exists jwt_private_key.pem && [[ -f "$DIR/jwt_public_key.pem" ]]; then
    echo "  conservé: secrets/jwt_private_key.pem, jwt_public_key.pem"
else
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$DIR/jwt_private_key.pem" 2>/dev/null
    openssl pkey -in "$DIR/jwt_private_key.pem" -pubout -out "$DIR/jwt_public_key.pem"
    publish jwt_private_key.pem
    publish jwt_public_key.pem
fi

if exists auth_users && [[ -f "$DIR/probe_password" ]]; then
    echo "  conservé: secrets/auth_users, probe_password"
else
    demo="$(random 20)"; probe="$(random 32)"; loadtest="$(random 20)"
    printf 'demo:%s:customer\nprobe:%s:probe\nloadtest:%s:customer\n' "$demo" "$probe" "$loadtest" > "$DIR/auth_users"
    printf '%s' "$probe" > "$DIR/probe_password"
    # Copies de consultation pour l'opérateur (non montées dans les conteneurs).
    printf '%s' "$demo" > "$DIR/demo_password"
    printf '%s' "$loadtest" > "$DIR/loadtest_password"
    publish auth_users
    publish probe_password
    chmod 600 "$DIR/demo_password" "$DIR/loadtest_password"
    echo "  généré  : secrets/demo_password, secrets/loadtest_password (lecture opérateur)"
fi

cat <<EOF

Terminé. Rappels :
  - ne jamais commiter ./secrets (déjà dans .gitignore) ;
  - partage au sein de l'équipe : voir security/secrets/README.md (SOPS + age) ;
  - mot de passe du compte "demo" : cat secrets/demo_password
EOF
