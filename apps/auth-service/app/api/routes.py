from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, ConfigDict, Field

from app.services.tokens import issue_token

router = APIRouter()
logger = logging.getLogger(__name__)

LOGIN_ATTEMPTS = Counter("auth_login_attempts_total", "Tentatives de connexion.", ["result"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    checks: dict[str, bool] = {}


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, request: Request) -> TokenResponse:
    settings = request.app.state.settings
    client_ip = request.client.host if request.client else "unknown"
    if not settings.private_key_pem:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Émission de jetons non configurée")
    user = request.app.state.users.authenticate(payload.username, payload.password)
    if user is None:
        LOGIN_ATTEMPTS.labels("failure").inc()
        logger.warning(
            "auth.login_failed",
            extra={"event": "auth.login_failed", "username": payload.username, "client_ip": client_ip},
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    LOGIN_ATTEMPTS.labels("success").inc()
    logger.info(
        "auth.login_succeeded",
        extra={"event": "auth.login_succeeded", "username": user.username, "client_ip": client_ip},
    )
    return TokenResponse(access_token=issue_token(user, settings), expires_in=settings.token_ttl_seconds)


@router.get("/health/live", response_model=Health, tags=["health"])
def live(request: Request) -> Health:
    return Health(status="ok", service=request.app.state.settings.service_name)


@router.get("/health/ready", response_model=Health, tags=["health"])
def ready(request: Request, response: Response) -> Health:
    checks = {
        "jwt_private_key": bool(request.app.state.settings.private_key_pem),
        "users_loaded": len(request.app.state.users) > 0,
    }
    healthy = all(checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(
        status="ok" if healthy else "degraded",
        service=request.app.state.settings.service_name,
        checks=checks,
    )


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
