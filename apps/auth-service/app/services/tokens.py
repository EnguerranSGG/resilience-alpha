from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings
from app.services.users import User


def issue_token(user: User, settings: Settings) -> str:
    if not settings.private_key_pem:
        raise RuntimeError("Clé privée JWT absente")
    now = datetime.now(UTC)
    claims = {
        "sub": user.username,
        "roles": list(user.roles),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=settings.token_ttl_seconds),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, settings.private_key_pem, algorithm="RS256")
