# Moteur de remédiation. Contexte de build : racine du dépôt (contrat partagé + playbooks).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/remediation/src \
    HOME=/tmp

WORKDIR /opt/remediation

COPY packages/resilience-contracts /tmp/resilience-contracts
COPY remediation/requirements.txt remediation/requirements-ansible.txt ./
RUN pip install /tmp/resilience-contracts -r requirements.txt -r requirements-ansible.txt \
    && rm -rf /tmp/resilience-contracts

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home app \
    && mkdir -p /var/log/resilience/remediation \
        /var/lib/gateway-control/requests /var/lib/gateway-control/status \
    && chown -R app:app /var/log/resilience /var/lib/gateway-control/requests \
    # Volume d'état : écrit par la passerelle (uid 101), lu ici en lecture seule.
    && chown 101:101 /var/lib/gateway-control/status

COPY remediation/src ./src
COPY infrastructure/ansible ./ansible

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"]

CMD ["uvicorn", "--factory", "remediation_engine.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
