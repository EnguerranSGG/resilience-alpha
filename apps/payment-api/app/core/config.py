from __future__ import annotations

from decimal import Decimal
from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


def read_secret(value: str | None, file: Path | None) -> str | None:
    """Retourne le secret fourni directement ou lu depuis un fichier (Docker secret)."""
    if value:
        return value
    if file and file.is_file():
        return file.read_text(encoding="utf-8").strip()
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAYMENT_", extra="ignore")

    service_name: str = "payment-api"
    log_level: str = "INFO"
    log_file: Path | None = None

    database_url: str | None = Field(
        default=None,
        description="URL complète (tests). En conteneur, préférer les variables DB_* et le secret.",
    )
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "payments"
    db_user: str = "payments"
    db_password: str | None = None
    db_password_file: Path | None = None
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=0, ge=0, le=50)
    db_pool_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    jwt_public_key: str | None = None
    jwt_public_key_file: Path | None = None
    jwt_issuer: str = "resilience-alpha-auth"
    jwt_audience: str = "resilience-alpha-payment"

    # Paramètre de laboratoire : coût de traitement simulé rendant la dégradation
    # observable sous une charge modérée et contrôlée.
    processing_delay_ms: int = Field(default=0, ge=0, le=5_000)
    max_amount: Decimal = Field(default=Decimal("10000.00"), gt=0)

    @cached_property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=read_secret(self.db_password, self.db_password_file),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @cached_property
    def public_key_pem(self) -> str | None:
        return read_secret(self.jwt_public_key, self.jwt_public_key_file)
