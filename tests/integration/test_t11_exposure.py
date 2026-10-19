"""T11 — les services sensibles ne sont pas publiés sur le réseau externe."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

INTERNAL_SERVICES = {
    "postgres",
    "payment-api",
    "auth-service",
    "frontend",
    "nginx-exporter",
    "prometheus",
    "loki",
    "alloy",
    "ml-detector",
    "remediation",
    "ollama",
}


def _load_compose(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _published_ports(service: dict) -> list[str]:
    ports = service.get("ports") or []
    return [str(item) for item in ports]


def test_t11_internal_services_have_no_published_ports(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    services = compose["services"]
    for name in INTERNAL_SERVICES:
        assert name in services, f"service {name} manquant dans compose.yml"
        ports = _published_ports(services[name])
        assert ports == [], f"{name} publie des ports : {ports}"


def test_t11_gateway_is_the_only_scenario_entrypoint(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    gateway_ports = _published_ports(compose["services"]["gateway"])
    assert len(gateway_ports) == 1
    assert "GATEWAY_BIND_ADDR" in gateway_ports[0]
    assert "GATEWAY_PORT" in gateway_ports[0]


def test_t11_grafana_is_bound_to_host_loopback_by_default(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    grafana_ports = _published_ports(compose["services"]["grafana"])
    assert len(grafana_ports) == 1
    assert "GRAFANA_BIND_ADDR" in grafana_ports[0]
    example = (repo_root / ".env.example").read_text(encoding="utf-8")
    assert "GRAFANA_BIND_ADDR=127.0.0.1" in example


def test_t11_rag_and_ollama_are_isolated(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    rag = compose["services"]["rag-assistant"]
    ollama = compose["services"]["ollama"]
    assert rag.get("profiles") == ["rag"]
    assert ollama.get("profiles") == ["rag"]
    rag_ports = _published_ports(rag)
    assert len(rag_ports) == 1
    assert rag_ports[0].startswith("127.0.0.1:")
    assert _published_ports(ollama) == []


def test_t11_sensitive_networks_are_internal(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    networks = compose["networks"]
    for name in ("apps", "backend", "observability", "control"):
        assert networks[name].get("internal") is True, name
    assert "internal" not in networks["edge"]


def test_t11_prometheus_dev_override_stays_on_loopback(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.dev.yml")
    ports = _published_ports(compose["services"]["prometheus"])
    assert ports == ["127.0.0.1:${PROMETHEUS_DEV_PORT:-9090}:9090"]


def test_t11_published_ports_do_not_bind_wildcard_addresses(repo_root: Path) -> None:
    compose = _load_compose(repo_root / "infrastructure" / "docker" / "compose.yml")
    for name, service in compose["services"].items():
        for port in _published_ports(service):
            assert "0.0.0.0" not in port, f"{name} publie {port}"
