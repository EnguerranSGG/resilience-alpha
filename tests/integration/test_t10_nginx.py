"""T10 — la configuration NGINX des profils est présente, cohérente et validable."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

PROFILES = ("normal", "mitigation")


def test_t10_profile_files_exist_and_set_gateway_profile(repo_root: Path) -> None:
    nginx_dir = repo_root / "infrastructure" / "nginx"
    for name in PROFILES:
        path = nginx_dir / f"{name}.conf"
        text = path.read_text(encoding="utf-8")
        assert f"set $gateway_profile {name};" in text
        assert "limit_req" in text
        assert "limit_conn" in text


def test_t10_mitigation_is_stricter_than_normal(repo_root: Path) -> None:
    nginx_dir = repo_root / "infrastructure" / "nginx"
    normal = (nginx_dir / "normal.conf").read_text(encoding="utf-8")
    mitigation = (nginx_dir / "mitigation.conf").read_text(encoding="utf-8")
    assert "per_ip_normal" in normal
    assert "per_ip_strict" in mitigation
    assert "limit_conn conn_per_ip 10;" in mitigation
    assert "limit_conn conn_per_ip 200;" in normal


def test_t10_gateway_overwrites_client_forwarded_headers(repo_root: Path) -> None:
    gateway = (repo_root / "infrastructure" / "nginx" / "gateway.conf").read_text(encoding="utf-8")
    assert "proxy_set_header X-Real-IP         $remote_addr;" in gateway
    assert "proxy_set_header X-Forwarded-For   $remote_addr;" in gateway
    assert "proxy_set_header X-Forwarded-For   $http_x_forwarded_for;" not in gateway


def test_t10_metrics_and_event_ingestion_are_not_proxied(repo_root: Path) -> None:
    gateway = (repo_root / "infrastructure" / "nginx" / "gateway.conf").read_text(encoding="utf-8")
    assert "location /api/metrics" not in gateway
    assert "location /api/remediation/events" not in gateway
    assert "location /api/remediation/" in gateway


@pytest.mark.live
def test_t10_nginx_t_succeeds_in_gateway_image(repo_root: Path, run) -> None:
    """Valide réellement `nginx -t` dans l'image de la passerelle (Docker requis)."""
    script = repo_root / "scripts" / "validate-nginx.sh"
    result = run(["bash", str(script)], timeout=180)
    stderr = result.stderr or ""
    if result.returncode != 0 and ("docker" in stderr.lower() or result.returncode == 127):
        pytest.skip(f"Docker indisponible pour T10 live : {stderr[:200]}")
    assert result.returncode == 0, (result.stdout or "") + stderr
