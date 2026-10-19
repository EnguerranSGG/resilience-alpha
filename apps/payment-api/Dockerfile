# Contexte de build : apps/payment-api
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home app \
    && mkdir -p /var/log/resilience/payment-api \
    && chown -R app:app /var/log/resilience

COPY app ./app

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"]

# --forwarded-allow-ips : seule l'adresse fixe de la passerelle est autorisée à
# transmettre X-Forwarded-For (voir infrastructure/docker/compose.yml).
CMD ["sh", "-c", "exec uvicorn --factory app.main:create_app --host 0.0.0.0 --port 8000 --no-access-log --proxy-headers --forwarded-allow-ips=${TRUSTED_PROXY_IP:-127.0.0.1}"]
