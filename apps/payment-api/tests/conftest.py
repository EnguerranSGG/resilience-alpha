from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture(scope="session")
def rsa_keys() -> tuple[str, str]:
    """Paire de clés éphémère générée pour les tests (jamais écrite sur disque)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture
def settings(rsa_keys: tuple[str, str]) -> Settings:
    return Settings(database_url="sqlite+pysqlite:///:memory:", jwt_public_key=rsa_keys[1])


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def make_token(rsa_keys: tuple[str, str], settings: Settings) -> Callable[..., str]:
    def _make(sub: str = "demo", expires_in: int = 300, audience: str | None = None) -> str:
        now = datetime.now(UTC)
        claims = {
            "sub": sub,
            "iss": settings.jwt_issuer,
            "aud": audience or settings.jwt_audience,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "roles": ["customer"],
        }
        return jwt.encode(claims, rsa_keys[0], algorithm="RS256")

    return _make


@pytest.fixture
def auth_headers(make_token: Callable[..., str]) -> Callable[..., dict[str, str]]:
    def _headers(idempotency_key: str | None = None, sub: str = "demo") -> dict[str, str]:
        headers = {"Authorization": f"Bearer {make_token(sub=sub)}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    return _headers
