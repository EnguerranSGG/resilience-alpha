"""Vérification des JWT émis par ``auth-service``.

Le service de paiement ne détient que la **clé publique** : il peut vérifier un
jeton mais pas en fabriquer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    roles: tuple[str, ...]


def decode_token(token: str, settings: Settings) -> AuthenticatedUser:
    if not settings.public_key_pem:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Vérification JWT non configurée")
    try:
        claims = jwt.decode(
            token,
            settings.public_key_pem,
            algorithms=["RS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Jeton invalide",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return AuthenticatedUser(user_id=str(claims["sub"]), roles=tuple(claims.get("roles", [])))


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials, request.app.state.settings)
