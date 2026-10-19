from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.api import health, payments
from app.core.config import Settings
from app.core.database import Base, build_engine, build_sessionmaker
from app.core.logging import configure_logging
from app.core.metrics import install_http_metrics

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level, settings.log_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings)
        app.state.engine = engine
        app.state.sessionmaker = build_sessionmaker(engine)
        try:
            # TODO(P1): remplacer create_all par des migrations Alembic.
            Base.metadata.create_all(engine)
        except OperationalError:
            logger.error("startup.database_unavailable", exc_info=True)
        logger.info("startup.complete", extra={"event": "startup.complete"})
        yield
        engine.dispose()

    app = FastAPI(
        title="RESILIENCE-ALPHA payment-api",
        version="0.1.0",
        description="API de paiement **fictive**. Aucune donnée financière réelle.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    install_http_metrics(app)
    app.include_router(health.router)
    app.include_router(payments.router)

    @app.exception_handler(PoolTimeoutError)
    @app.exception_handler(OperationalError)
    async def _database_unavailable(request: Request, exc: Exception) -> JSONResponse:
        logger.warning(
            "payment.database_unavailable",
            extra={"event": "payment.database_unavailable", "error": type(exc).__name__},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service temporairement indisponible"},
            headers={"Retry-After": "2"},
        )

    return app
