from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.payment import IDEMPOTENCY_KEY_PATTERN, PaymentCreate, PaymentList, PaymentRead
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]


@router.post(
    "",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Requête rejouée : transaction existante renvoyée"},
        409: {"description": "Clé d'idempotence déjà utilisée pour un contenu différent"},
    },
)
def create_payment(
    request: Request,
    response: Response,
    payload: PaymentCreate,
    session: SessionDep,
    user: UserDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", pattern=IDEMPOTENCY_KEY_PATTERN)],
) -> PaymentRead:
    try:
        payment, created = payment_service.create_payment(
            session, request.app.state.settings, user.user_id, idempotency_key, payload
        )
    except payment_service.IdempotencyConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Clé d'idempotence déjà utilisée pour une autre demande") from exc
    if not created:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replayed"] = "true"
    return PaymentRead.model_validate(payment)


@router.get("", response_model=PaymentList)
def list_payments(session: SessionDep, user: UserDep, limit: Annotated[int, Query(ge=1, le=100)] = 20) -> PaymentList:
    items = payment_service.list_payments(session, user.user_id, limit)
    return PaymentList(items=[PaymentRead.model_validate(p) for p in items])


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: uuid.UUID, session: SessionDep, user: UserDep) -> PaymentRead:
    payment = payment_service.get_payment(session, user.user_id, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction introuvable")
    return PaymentRead.model_validate(payment)
