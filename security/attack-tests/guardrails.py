"""Garde-fous du test de charge contrôlé (scénario DoS de laboratoire).

Module sans dépendance à Locust, testé unitairement. Toute violation lève
``GuardrailError`` AVANT le moindre envoi de requête.

Règles :
* aucune cible par défaut ; la cible doit être explicitement listée dans
  ``LOADTEST_AUTHORIZED_TARGETS`` ;
* la cible est une adresse IP privée/locale du laboratoire (ou ``localhost``),
  jamais un nom DNS ni une adresse publique ;
* durée, nombre d'utilisateurs virtuels, vitesse de montée et débit par
  utilisateur sont obligatoires et plafonnés ;
* aucun mode distribué (master/worker), aucune falsification d'en-têtes.
"""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

MAX_USERS = 50
MAX_SPAWN_RATE = 10
MAX_RUN_TIME_SECONDS = 300
MAX_RPS_PER_USER = 10.0
MAX_TOTAL_RPS = 300.0
USER_AGENT = "resilience-alpha-loadtest/1.0 (laboratoire EPSI, test autorisé)"


class GuardrailError(ValueError):
    """Configuration refusée : le test ne doit pas démarrer."""


@dataclass(frozen=True)
class LoadTestConfig:
    target: str
    users: int
    spawn_rate: int
    run_time_seconds: int
    rps_per_user: float
    username: str

    @property
    def max_total_rps(self) -> float:
        return self.users * self.rps_per_user


def _require(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise GuardrailError(f"{name} est obligatoire (aucune valeur par défaut)")
    return value


def _int(env: Mapping[str, str], name: str, low: int, high: int) -> int:
    raw = _require(env, name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise GuardrailError(f"{name} doit être un entier : {raw!r}") from exc
    if not low <= value <= high:
        raise GuardrailError(f"{name}={value} hors limites [{low}, {high}]")
    return value


def _float(env: Mapping[str, str], name: str, low: float, high: float) -> float:
    raw = _require(env, name)
    try:
        value = float(raw)
    except ValueError as exc:
        raise GuardrailError(f"{name} doit être un nombre : {raw!r}") from exc
    if not low < value <= high:
        raise GuardrailError(f"{name}={value} hors limites ]{low}, {high}]")
    return value


def normalize_target(url: str) -> str:
    """Vérifie la forme de la cible et la renvoie sous forme canonique ``http://ip:port``."""
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"}:
        raise GuardrailError(f"schéma non autorisé : {parts.scheme!r} (http ou https)")
    if parts.username or parts.password:
        raise GuardrailError("identifiants interdits dans l'URL cible")
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        raise GuardrailError("la cible doit être une origine (schéma://hôte:port), sans chemin")
    host = parts.hostname or ""
    if host == "localhost":
        address = ipaddress.ip_address("127.0.0.1")
    else:
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise GuardrailError(f"la cible doit être une adresse IP de laboratoire, pas un nom : {host!r}") from exc
    if not (address.is_private or address.is_loopback) or address.is_multicast or address.is_unspecified:
        raise GuardrailError(f"adresse non privée refusée : {address}")
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as exc:
        raise GuardrailError("port invalide") from exc
    shown = f"[{address}]" if address.version == 6 else str(address)
    return f"{parts.scheme}://{shown}:{port}"


def load_config(env: Mapping[str, str] | None = None) -> LoadTestConfig:
    env = os.environ if env is None else env
    target = normalize_target(_require(env, "LOADTEST_TARGET"))
    authorized = {
        normalize_target(item) for item in _require(env, "LOADTEST_AUTHORIZED_TARGETS").split(",") if item.strip()
    }
    if target not in authorized:
        raise GuardrailError(f"cible {target} absente de LOADTEST_AUTHORIZED_TARGETS")

    config = LoadTestConfig(
        target=target,
        users=_int(env, "LOADTEST_USERS", 1, MAX_USERS),
        spawn_rate=_int(env, "LOADTEST_SPAWN_RATE", 1, MAX_SPAWN_RATE),
        run_time_seconds=_int(env, "LOADTEST_RUN_TIME_SECONDS", 10, MAX_RUN_TIME_SECONDS),
        rps_per_user=_float(env, "LOADTEST_RPS_PER_USER", 0, MAX_RPS_PER_USER),
        username=env.get("LOADTEST_USERNAME", "loadtest").strip() or "loadtest",
    )
    if config.max_total_rps > MAX_TOTAL_RPS:
        raise GuardrailError(f"débit théorique {config.max_total_rps:.0f} req/s > plafond {MAX_TOTAL_RPS:.0f}")
    return config


def check_runtime(
    config: LoadTestConfig, *, host: str | None, users: int | None, run_time: int | None, distributed: bool
) -> None:
    """Contrôle les options effectives de Locust (aucun contournement par la ligne de commande)."""
    if distributed:
        raise GuardrailError("mode distribué (master/worker) interdit")
    if host is None or normalize_target(host) != config.target:
        raise GuardrailError(f"hôte Locust {host!r} différent de la cible autorisée {config.target}")
    if users is None or users > config.users:
        raise GuardrailError(f"utilisateurs Locust {users} > LOADTEST_USERS={config.users}")
    if run_time is None or run_time > config.run_time_seconds:
        raise GuardrailError(f"durée Locust {run_time} s absente ou > {config.run_time_seconds} s")


def summary(config: LoadTestConfig) -> str:
    return (
        f"cible={config.target} utilisateurs={config.users} montée={config.spawn_rate}/s "
        f"durée={config.run_time_seconds}s débit≤{config.max_total_rps:.0f} req/s"
    )


if __name__ == "__main__":
    import sys

    try:
        print(summary(load_config()))
    except GuardrailError as error:
        print(f"REFUS : {error}", file=sys.stderr)
        raise SystemExit(2) from error
