# Détecteur ML. Contexte de build : racine du dépôt (contrat partagé).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/detector/src

WORKDIR /opt/detector

COPY packages/resilience-contracts /tmp/resilience-contracts
COPY ai/anomaly-detection/requirements.txt .
RUN pip install /tmp/resilience-contracts -r requirements.txt && rm -rf /tmp/resilience-contracts

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home app \
    && mkdir -p /opt/detector/models /opt/detector/data \
    && chown -R app:app /opt/detector/models /opt/detector/data

COPY ai/anomaly-detection/src ./src

USER 10001
EXPOSE 8000

CMD ["python", "-m", "anomaly_detection.main"]
