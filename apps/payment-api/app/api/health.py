from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.core.metrics import DATABASE_UP
from app.schemas.health import HealthStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health/live", response_model=HealthStatus, tags=["health"])
def live(request: Request) -> HealthStatus:
    return HealthStatus(status="ok", service=request.app.state.settings.service_name)


@router.get("/health/ready", response_model=HealthStatus, tags=["health"])
def ready(request: Request, response: Response) -> HealthStatus:
    settings = request.app.state.settings
    checks = {"database": False, "jwt_public_key": bool(settings.public_key_pem)}
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        logger.warning("health.database_unavailable", exc_info=True)
    DATABASE_UP.set(1 if checks["database"] else 0)
    healthy = all(checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthStatus(status="ok" if healthy else "degraded", service=settings.service_name, checks=checks)


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
