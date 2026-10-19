#!/usr/bin/env bash
# Vérifie les prérequis du PC Hôte ou d'un poste de développement. N'installe rien.
set -uo pipefail

ok=0; warn=0; ko=0
pass()  { printf '  [OK]   %s\n' "$1"; ok=$((ok + 1)); }
note()  { printf '  [WARN] %s\n' "$1"; warn=$((warn + 1)); }
fail()  { printf '  [KO]   %s\n' "$1"; ko=$((ko + 1)); }

version_of() { "$@" 2>/dev/null | head -n1; }

echo "== Outils obligatoires"
if command -v docker >/dev/null; then
    pass "docker : $(version_of docker --version)"
    if docker info >/dev/null 2>&1; then pass "démon Docker joignable"; else fail "démon Docker arrêté (lancer Docker Desktop)"; fi
    if docker compose version >/dev/null 2>&1; then pass "$(version_of docker compose version)"; else fail "plugin docker compose absent"; fi
else
    fail "docker absent"
fi
command -v openssl >/dev/null && pass "openssl : $(version_of openssl version)" || fail "openssl absent (génération des secrets)"
command -v git >/dev/null && pass "git : $(version_of git --version)" || fail "git absent"
command -v make >/dev/null && pass "make : $(version_of make --version)" || note "make absent : utiliser les commandes docker compose du README"
command -v curl >/dev/null && pass "curl présent" || note "curl absent (smoke tests)"

echo "== Outils de développement (facultatifs)"
for py in python3.12 python3.13 python3; do
    if command -v "$py" >/dev/null; then
        v="$("$py" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        if "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then pass "$py ($v)"; else note "$py ($v) < 3.12"; fi
        break
    fi
done
if command -v node >/dev/null; then
    major="$(node -p 'process.versions.node.split(".")[0]')"
    if [[ "$major" == "24" || "$major" == "22" || "$major" -ge 24 ]]; then pass "node $(node --version)"; else note "node $(node --version) : version LTS 24 recommandée"; fi
else
    note "node absent (le frontend se construit aussi dans Docker)"
fi
command -v ansible-playbook >/dev/null && pass "ansible-playbook présent" || note "ansible absent sur l'hôte (seul deploy.yml l'utilise ; la remédiation l'embarque)"
command -v sops >/dev/null && pass "sops présent" || note "sops absent (partage chiffré des secrets)"
command -v age >/dev/null && pass "age présent" || note "age absent (clé SOPS)"

echo "== Configuration du dépôt"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ -f "$ROOT/.env" ]] && pass ".env présent" || note ".env absent : cp .env.example .env"
for s in postgres_password jwt_private_key.pem jwt_public_key.pem auth_users probe_password remediation_event_token grafana_admin_password; do
    [[ -f "$ROOT/secrets/$s" ]] || { note "secret manquant : secrets/$s (./scripts/generate-secrets.sh)"; continue; }
done
[[ -f "$ROOT/ai/anomaly-detection/models/isolation_forest.joblib" ]] \
    && pass "modèle ML présent" || note "aucun modèle ML : le détecteur n'émettra aucun événement"

echo "== Ressources"
if [[ "$(uname -s)" == "Linux" ]] && [[ -r /proc/meminfo ]]; then
    mem_gb=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
    (( mem_gb >= 15 )) && pass "RAM visible : ${mem_gb} Go" || note "RAM visible : ${mem_gb} Go (16 Go recommandés, voir .wslconfig)"
fi
if grep -qi microsoft /proc/version 2>/dev/null; then
    pass "WSL2 détecté"
    [[ "$ROOT" == /mnt/* ]] && note "dépôt sous /mnt/c : performances Docker réduites, cloner dans ~/ (système de fichiers Linux)"
fi

echo
echo "Bilan : $ok OK, $warn avertissement(s), $ko bloquant(s)"
(( ko == 0 ))
