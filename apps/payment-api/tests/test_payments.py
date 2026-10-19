"""T03/T04 (partie unitaire) — enregistrement et idempotence des transactions fictives."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi.testclient import TestClient

Headers = Callable[..., dict[str, str]]


def _key() -> str:
    return f"test-{uuid.uuid4().hex[:16]}"


def test_create_payment_is_completed(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/payments", json={"amount": "12.50", "currency": "EUR"}, headers=auth_headers(_key()))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["amount"] == "12.50"
    assert body["user_id"] == "demo"
    assert body["created_at"].endswith(("Z", "+00:00"))


def test_get_payment_roundtrip(client: TestClient, auth_headers: Headers) -> None:
    created = client.post("/payments", json={"amount": "3.10"}, headers=auth_headers(_key())).json()
    fetched = client.get(f"/payments/{created['id']}", headers=auth_headers())
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_same_idempotency_key_is_not_duplicated(client: TestClient, auth_headers: Headers) -> None:
    key = _key()
    first = client.post("/payments", json={"amount": "10.00"}, headers=auth_headers(key))
    second = client.post("/payments", json={"amount": "10"}, headers=auth_headers(key))
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["Idempotent-Replayed"] == "true"
    assert second.json()["id"] == first.json()["id"]
    items = client.get("/payments", headers=auth_headers()).json()["items"]
    assert [p["idempotency_key"] for p in items].count(key) == 1


def test_reused_key_with_different_payload_conflicts(client: TestClient, auth_headers: Headers) -> None:
    key = _key()
    client.post("/payments", json={"amount": "10.00"}, headers=auth_headers(key))
    response = client.post("/payments", json={"amount": "99.00"}, headers=auth_headers(key))
    assert response.status_code == 409


def test_idempotency_key_is_scoped_per_user(client: TestClient, auth_headers: Headers) -> None:
    key = _key()
    a = client.post("/payments", json={"amount": "1.00"}, headers=auth_headers(key, sub="alice"))
    b = client.post("/payments", json={"amount": "1.00"}, headers=auth_headers(key, sub="bob"))
    assert a.status_code == b.status_code == 201
    assert a.json()["id"] != b.json()["id"]


def test_user_cannot_read_other_user_payment(client: TestClient, auth_headers: Headers) -> None:
    created = client.post("/payments", json={"amount": "1.00"}, headers=auth_headers(_key(), sub="alice")).json()
    response = client.get(f"/payments/{created['id']}", headers=auth_headers(sub="mallory"))
    assert response.status_code == 404


def test_amount_above_limit_fails_business_rule(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/payments", json={"amount": "10000.01"}, headers=auth_headers(_key()))
    assert response.status_code == 201
    assert response.json()["status"] == "FAILED"
    assert response.json()["failure_reason"] == "AMOUNT_LIMIT_EXCEEDED"


def test_invalid_amounts_are_rejected(client: TestClient, auth_headers: Headers) -> None:
    for amount in ("0", "-5.00", "1.001", "abc"):
        response = client.post("/payments", json={"amount": amount}, headers=auth_headers(_key()))
        assert response.status_code == 422, amount


def test_unknown_fields_are_rejected(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/payments", json={"amount": "1.00", "status": "COMPLETED"}, headers=auth_headers(_key()))
    assert response.status_code == 422


def test_idempotency_key_is_required(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/payments", json={"amount": "1.00"}, headers=auth_headers())
    assert response.status_code == 422


def test_authentication_is_required(client: TestClient) -> None:
    response = client.post("/payments", json={"amount": "1.00"}, headers={"Idempotency-Key": _key()})
    assert response.status_code == 401


def test_expired_or_foreign_tokens_are_rejected(client: TestClient, make_token: Callable[..., str]) -> None:
    for token in (make_token(expires_in=-10), make_token(audience="other-service"), "not-a-jwt"):
        response = client.get("/payments", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_unknown_payment_returns_404(client: TestClient, auth_headers: Headers) -> None:
    response = client.get(f"/payments/{uuid.uuid4()}", headers=auth_headers())
    assert response.status_code == 404
