"""Vérification métier du rétablissement.

La reprise n'est validée que si un parcours utilisateur complet réussit **via la
passerelle publique** (même chemin qu'un utilisateur légitime) :

1. ``GET /api/health/ready`` répond 200 ;
2. connexion du compte de sonde ``probe`` ;
3. ``POST /api/payments`` avec une clé d'idempotence neuve → 201 et ``COMPLETED`` ;
4. rejeu de la même clé → 200, même identifiant (aucun doublon) ;
5. ``GET /api/payments/{id}`` → 200.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    passed: bool
    attempts: int
    steps: list[str] = field(default_factory=list)
    payment_id: str | None = None


class VerificationError(RuntimeError):
    pass


class BusinessVerifier:
    def __init__(
        self,
        gateway_url: str,
        username: str,
        password: str | None,
        timeout: float,
        attempts: int,
        delay_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.gateway_url = gateway_url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.attempts = attempts
        self.delay_seconds = delay_seconds
        self.transport = transport

    def _check(self, condition: bool, message: str, steps: list[str]) -> None:
        if not condition:
            raise VerificationError(message)
        steps.append(message)

    def _run_once(self) -> VerificationResult:
        steps: list[str] = []
        if not self.password:
            raise VerificationError("mot de passe du compte de sonde absent")
        with httpx.Client(base_url=self.gateway_url, timeout=self.timeout, transport=self.transport) as client:
            ready = client.get("/api/health/ready")
            self._check(ready.status_code == 200, f"ready={ready.status_code}", steps)

            login = client.post("/auth/login", json={"username": self.username, "password": self.password})
            self._check(login.status_code == 200, f"login={login.status_code}", steps)
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            key = f"probe-{uuid.uuid4().hex}"
            body = {"amount": "0.01", "currency": "EUR", "description": "remediation-probe"}
            created = client.post("/api/payments", json=body, headers=headers | {"Idempotency-Key": key})
            self._check(created.status_code == 201, f"create={created.status_code}", steps)
            payment = created.json()
            self._check(payment.get("status") == "COMPLETED", f"status={payment.get('status')}", steps)

            replay = client.post("/api/payments", json=body, headers=headers | {"Idempotency-Key": key})
            self._check(
                replay.status_code == 200 and replay.json().get("id") == payment["id"],
                f"replay={replay.status_code} sans doublon",
                steps,
            )

            fetched = client.get(f"/api/payments/{payment['id']}", headers=headers)
            self._check(fetched.status_code == 200, f"get={fetched.status_code}", steps)
        return VerificationResult(True, 1, steps, payment["id"])

    def verify(self) -> VerificationResult:
        last_steps: list[str] = []
        for attempt in range(1, self.attempts + 1):
            try:
                result = self._run_once()
                result.attempts = attempt
                logger.info(
                    "verification.passed",
                    extra={"event": "verification.passed", "attempt": attempt, "steps": result.steps},
                )
                return result
            except (VerificationError, httpx.HTTPError, KeyError, ValueError) as exc:
                last_steps = [f"tentative {attempt} : {exc}"]
                logger.warning(
                    "verification.attempt_failed",
                    extra={"event": "verification.attempt_failed", "attempt": attempt, "error": str(exc)},
                )
                if attempt < self.attempts:
                    time.sleep(self.delay_seconds)
        return VerificationResult(False, self.attempts, last_steps)
