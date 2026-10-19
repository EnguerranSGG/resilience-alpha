"""Logique métier des paiements fictifs.

Idempotence : le couple (``user_id``, ``idempotency_key``) est unique en base.
Une requête rejouée avec la même clé et le même contenu renvoie la transaction
existante ; avec un contenu différent, elle est refusée (conflit).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.metrics import PAYMENTS_PROCESSED, PAYMENTS_REPLAYED
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate

logger = logging.getLogger(__name__)


class IdempotencyConflictError(Exception):
    """La clé d'idempotence a déjà servi pour une demande différente."""


def fingerprint(data: PaymentCreate) -> str:
    canonical = json.dumps(
        {
            "amount": str(data.amount.quantize(Decimal("0.01"))),
            "currency": data.currency,
            "description": data.description,
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _find_by_key(session: Session, user_id: str, key: str) -> Payment | None:
    return session.scalar(select(Payment).where(Payment.user_id == user_id, Payment.idempotency_key == key))


def _replay(existing: Payment, request_fingerprint: str) -> Payment:
    if existing.request_fingerprint != request_fingerprint:
        logger.warning(
            "payment.idempotency_conflict",
            extra={"event": "payment.idempotency_conflict", "payment_id": str(existing.id)},
        )
        raise IdempotencyConflictError
    PAYMENTS_REPLAYED.inc()
    logger.info("payment.replayed", extra={"event": "payment.replayed", "payment_id": str(existing.id)})
    return existing


def create_payment(
    session: Session, settings: Settings, user_id: str, idempotency_key: str, data: PaymentCreate
) -> tuple[Payment, bool]:
    """Crée et traite un paiement. Retourne ``(paiement, créé)``."""
    request_fingerprint = fingerprint(data)
    existing = _find_by_key(session, user_id, idempotency_key)
    if existing is not None:
        return _replay(existing, request_fingerprint), False

    payment = Payment(
        user_id=user_id,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        status=PaymentStatus.PENDING,
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
    )
    session.add(payment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        concurrent = _find_by_key(session, user_id, idempotency_key)
        if concurrent is None:
            raise
        return _replay(concurrent, request_fingerprint), False

    _process(payment, settings)
    session.commit()
    PAYMENTS_PROCESSED.labels(payment.status.value).inc()
    logger.info(
        "payment.processed",
        extra={
            "event": "payment.processed",
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "user_id": user_id,
        },
    )
    return payment, True


def _process(payment: Payment, settings: Settings) -> None:
    """Traitement simulé : aucune interaction avec un système financier réel."""
    if settings.processing_delay_ms:
        time.sleep(settings.processing_delay_ms / 1000)
    if payment.amount > settings.max_amount:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = "AMOUNT_LIMIT_EXCEEDED"
    else:
        payment.status = PaymentStatus.COMPLETED


def get_payment(session: Session, user_id: str, payment_id: uuid.UUID) -> Payment | None:
    return session.scalar(select(Payment).where(Payment.id == payment_id, Payment.user_id == user_id))


def list_payments(session: Session, user_id: str, limit: int) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc()).limit(limit)
        )
    )
