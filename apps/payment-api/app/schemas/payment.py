from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.payment import PaymentStatus

IDEMPOTENCY_KEY_PATTERN = r"^[A-Za-z0-9_-]{8,64}$"

Currency = Literal["EUR", "USD", "GBP", "CHF"]


class PaymentCreate(BaseModel):
    """Demande de paiement fictif. Préférer un montant sous forme de chaîne ("12.50")."""

    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency = "EUR"
    description: str | None = Field(default=None, max_length=140)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: str
    amount: Decimal
    currency: str
    description: str | None
    status: PaymentStatus
    failure_reason: str | None
    idempotency_key: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _ensure_utc(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)


class PaymentList(BaseModel):
    items: list[PaymentRead]
