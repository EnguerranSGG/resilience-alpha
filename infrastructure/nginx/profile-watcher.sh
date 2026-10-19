#!/bin/sh
# Applique un profil NGINX prévalidé demandé par le moteur de remédiation.
#
# Entrée  : /etc/nginx/control/requests/request.json  (écrit par Ansible, volume dédié)
#           {"request_id": "<[A-Za-z0-9-]{8,64}>", "profile": "normal|mitigation"}
# Sortie  : /etc/nginx/control/status/status.json      (lu par Ansible)
#
# Le demandeur ne fournit qu'un NOM de profil ; le contenu vient exclusivement de
# /etc/nginx/profiles (image, lecture seule). `nginx -t` est exécuté avant tout
# rechargement ; en cas d'échec le profil précédent est restauré.
set -u

REQUEST=/etc/nginx/control/requests/request.json
STATUS_DIR=/etc/nginx/control/status
ACTIVE=/etc/nginx/active/profile.conf
PROFILES=/etc/nginx/profiles
INTERVAL="${PROFILE_WATCH_INTERVAL:-1}"

log() {
    printf '{"ts":"%s","service":"gateway","log_type":"control","msg":"%s"}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" | tee -a /var/log/gateway/control.log >&2
}

write_status() {
    tmp="$STATUS_DIR/.status.json.tmp"
    printf '{"request_id": "%s", "profile": "%s", "result": "%s", "message": "%s", "at": "%s"}\n' \
        "$1" "$2" "$3" "$4" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$tmp" && mv "$tmp" "$STATUS_DIR/status.json"
    log "profile request_id=$1 profile=$2 result=$3 ($4)"
}

checksum() { md5sum "$REQUEST" 2>/dev/null | cut -d' ' -f1; }

# Au démarrage, la passerelle part toujours du profil normal (voir docs/architecture/remediation.md).
last="$(checksum)"
write_status "boot" "normal" "applied" "démarrage sur le profil normal"

while true; do
    sleep "$INTERVAL"
    [ -f "$REQUEST" ] || continue
    current="$(checksum)"
    [ "$current" = "$last" ] && continue
    last="$current"

    rid="$(sed -n 's/.*"request_id": *"\([A-Za-z0-9-]\{8,64\}\)".*/\1/p' "$REQUEST")"
    profile="$(sed -n 's/.*"profile": *"\([a-z]\{1,32\}\)".*/\1/p' "$REQUEST")"

    if [ -z "$rid" ]; then
        write_status "invalid" "none" "rejected" "request_id absent ou invalide"
        continue
    fi
    case "$profile" in
        normal|mitigation) ;;
        *) write_status "$rid" "none" "rejected" "profil hors liste blanche"; continue ;;
    esac

    cp "$ACTIVE" "$ACTIVE.previous"
    cp "$PROFILES/$profile.conf" "$ACTIVE"
    if nginx -t >/tmp/nginx-test.log 2>&1 && nginx -s reload >>/tmp/nginx-test.log 2>&1; then
        write_status "$rid" "$profile" "applied" "configuration testée puis rechargée"
    else
        cp "$ACTIVE.previous" "$ACTIVE"
        write_status "$rid" "$profile" "failed" "nginx -t ou reload en échec, profil précédent conservé"
    fi
done
