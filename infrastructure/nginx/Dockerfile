# Passerelle WAF + reverse proxy. Contexte de build : infrastructure/
FROM owasp/modsecurity-crs:4.25.2-nginx-alpine-lts

USER root

# Remplace le vhost générique de l'image par la configuration RESILIENCE-ALPHA.
RUN rm -f /etc/nginx/conf.d/default.conf \
    && mkdir -p /etc/nginx/profiles /etc/nginx/active \
        /etc/nginx/control/requests /etc/nginx/control/status /var/log/gateway \
    && chown nginx:nginx /etc/nginx/active /etc/nginx/control/status /var/log/gateway \
    # Volume des demandes : écrit par le moteur de remédiation (uid 10001), lu par nginx.
    && chown 10001:10001 /etc/nginx/control/requests

COPY nginx/default.conf.template /etc/nginx/templates/conf.d/default.conf.template
COPY nginx/gateway.conf /etc/nginx/conf.d/gateway.conf
COPY nginx/normal.conf nginx/mitigation.conf /etc/nginx/profiles/
COPY --chown=nginx:nginx nginx/normal.conf /etc/nginx/active/profile.conf
COPY waf/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf /etc/modsecurity.d/owasp-crs/rules/
COPY nginx/profile-watcher.sh /usr/local/bin/profile-watcher.sh
COPY nginx/99-start-profile-watcher.sh /docker-entrypoint.d/99-start-profile-watcher.sh
RUN chmod 0444 /etc/nginx/profiles/*.conf /etc/nginx/conf.d/gateway.conf \
    && chmod 0555 /usr/local/bin/profile-watcher.sh /docker-entrypoint.d/99-start-profile-watcher.sh

USER nginx

ENV MODSEC_AUDIT_LOG=/var/log/gateway/modsec_audit.log \
    MODSEC_AUDIT_LOG_FORMAT=JSON \
    MODSEC_AUDIT_LOG_PARTS=AFHZ \
    MODSEC_AUDIT_LOG_RELEVANT_STATUS="^(?:5|403)" \
    BLOCKING_PARANOIA=1 \
    ANOMALY_INBOUND=5 \
    ANOMALY_OUTBOUND=4

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1
