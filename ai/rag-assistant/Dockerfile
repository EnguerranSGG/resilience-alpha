# Assistant RAG. Contexte de build : ai/rag-assistant
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/rag/src

WORKDIR /opt/rag

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home app \
    && mkdir -p /opt/rag/index && chown app:app /opt/rag/index

COPY src ./src
COPY documents ./documents

USER 10001
EXPOSE 8000

CMD ["uvicorn", "--factory", "rag_assistant.api:create_app", "--host", "0.0.0.0", "--port", "8000"]
