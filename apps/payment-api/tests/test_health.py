"""T02 (partie unitaire) — l'API de paiement répond aux healthchecks."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_live(client: TestClient) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_with_database(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"] == {"database": True, "jwt_public_key": True}


def test_ready_reports_missing_jwt_key() -> None:
    settings = Settings(database_url="sqlite+pysqlite:///:memory:")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["jwt_public_key"] is False


def test_metrics_exposes_http_series(client: TestClient) -> None:
    client.get("/health/live")
    body = client.get("/metrics").text
    assert 'http_requests_total{method="GET",route="/health/live",status="200"}' in body
    assert "http_request_duration_seconds_bucket" in body
    assert "http_requests_in_progress" in body
    assert "process_cpu_seconds_total" in body or "python_info" in body


def test_unknown_route_label_is_bounded(client: TestClient) -> None:
    client.get("/random-attacker-path-123")
    body = client.get("/metrics").text
    assert 'route="unmatched"' in body
    assert "random-attacker-path-123" not in body
