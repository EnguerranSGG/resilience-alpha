from __future__ import annotations

from collections.abc import Iterator

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.users import InvalidUserSpecError, UserStore

TEST_PASSWORD = "test-only-password-123"


@pytest.fixture(scope="module")
def keys() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture
def settings(keys: tuple[str, str]) -> Settings:
    return Settings(jwt_private_key=keys[0], users=f"demo:{TEST_PASSWORD}\nprobe:{TEST_PASSWORD}:probe")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as c:
        yield c


def test_login_issues_verifiable_rs256_token(client: TestClient, keys: tuple[str, str], settings: Settings) -> None:
    response = client.post("/auth/login", json={"username": "demo", "password": TEST_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    claims = jwt.decode(
        body["access_token"],
        keys[1],
        algorithms=["RS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    assert claims["sub"] == "demo"
    assert claims["roles"] == ["customer"]
    assert body["expires_in"] == settings.token_ttl_seconds


def test_roles_are_propagated(client: TestClient, keys: tuple[str, str]) -> None:
    token = client.post("/auth/login", json={"username": "probe", "password": TEST_PASSWORD}).json()["access_token"]
    assert jwt.decode(token, options={"verify_signature": False})["roles"] == ["probe"]


@pytest.mark.parametrize(("username", "password"), [("demo", "wrong-password-xx"), ("ghost", TEST_PASSWORD)])
def test_bad_credentials_are_rejected(client: TestClient, username: str, password: str) -> None:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 401


def test_ready_without_secrets_is_degraded() -> None:
    with TestClient(create_app(Settings())) as c:
        assert c.get("/health/live").status_code == 200
        ready = c.get("/health/ready")
        login = c.post("/auth/login", json={"username": "demo", "password": "x" * 12})
    assert ready.status_code == 503
    assert login.status_code == 503


def test_ready_with_secrets(client: TestClient) -> None:
    assert client.get("/health/ready").json()["checks"] == {
        "jwt_private_key": True,
        "users_loaded": True,
    }


@pytest.mark.parametrize("spec", ["demo", "demo:short", "Bad User:" + "x" * 12])
def test_invalid_user_spec_is_refused(spec: str) -> None:
    with pytest.raises(InvalidUserSpecError):
        UserStore.from_spec(spec)


def test_metrics_counts_logins(client: TestClient) -> None:
    client.post("/auth/login", json={"username": "demo", "password": "nope-nope-nope"})
    assert 'auth_login_attempts_total{result="failure"}' in client.get("/metrics").text
