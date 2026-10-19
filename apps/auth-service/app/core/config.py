from __future__ import annotations

from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def read_secret(value: str | None, file: Path | None) -> str | None:
    if value:
        return value
    if file and file.is_file():
        return file.read_text(encoding="utf-8").strip()
    return None


class Settings(BaseSettings):
    """Configuration issue exclusivement de l'environnement et des Docker secrets.

    Aucune valeur par défaut ne fournit de clé ou de mot de passe : sans secret,
    le service démarre mais ``/health/ready`` répond 503 et la connexion est refusée.
    """

    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")

    service_name: str = "auth-service"
    log_level: str = "INFO"
    log_file: Path | None = None

    jwt_private_key: str | None = None
    jwt_private_key_file: Path | None = None
    jwt_issuer: str = "resilience-alpha-auth"
    jwt_audience: str = "resilience-alpha-payment"
    token_ttl_seconds: int = Field(default=900, ge=60, le=3600)

    users: str | None = Field(
        default=None, description="Lignes 'utilisateur:motdepasse[:role,role]' (tests uniquement)."
    )
    users_file: Path | None = None

    @cached_property
    def private_key_pem(self) -> str | None:
        return read_secret(self.jwt_private_key, self.jwt_private_key_file)

    @cached_property
    def users_spec(self) -> str | None:
        return read_secret(self.users, self.users_file)
