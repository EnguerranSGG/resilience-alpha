"""Test de charge contrôlé RESILIENCE-ALPHA (à lancer via ``run-loadtest.sh``).

Simule un afflux de clients authentifiés créant des paiements FICTIFS sur
la plateforme de laboratoire. Ne s'exécute jamais automatiquement.
Arrêt immédiat : Ctrl+C (ou fin de --run-time).
"""

from __future__ import annotations

import os
import random
import time
import uuid
from pathlib import Path

from guardrails import USER_AGENT, GuardrailError, check_runtime, load_config, summary
from locust import HttpUser, constant_throughput, events, task
from locust.runners import MasterRunner, WorkerRunner

try:
    CONFIG = load_config()
except GuardrailError as error:
    raise SystemExit(f"REFUS : {error}") from error


def _password() -> str:
    path = os.environ.get("LOADTEST_PASSWORD_FILE", "")
    if not path or not Path(path).is_file():
        raise SystemExit("LOADTEST_PASSWORD_FILE doit pointer vers le mot de passe du compte loadtest")
    return Path(path).read_text(encoding="utf-8").strip()


PASSWORD = _password()
LOGIN_ATTEMPTS = 15


@events.init.add_listener
def _enforce(environment, **_kwargs) -> None:
    options = environment.parsed_options
    try:
        check_runtime(
            CONFIG,
            host=environment.host,
            users=getattr(options, "num_users", None),
            run_time=getattr(options, "run_time", None),
            distributed=isinstance(environment.runner, MasterRunner | WorkerRunner),
        )
    except GuardrailError as error:
        print(f"REFUS : {error}")
        environment.process_exit_code = 2
        if environment.runner is not None:
            environment.runner.quit()
        raise SystemExit(2) from error
    print(f"Test de charge autorisé : {summary(CONFIG)}")


class PaymentClient(HttpUser):
    host = CONFIG.target
    wait_time = constant_throughput(CONFIG.rps_per_user)

    def on_start(self) -> None:
        self.client.headers["User-Agent"] = USER_AGENT
        self.token: str | None = None
        # /auth/login est limité à 2 req/s par IP : on patiente au lieu d'abandonner.
        for attempt in range(LOGIN_ATTEMPTS):
            with self.client.post(
                "/auth/login",
                json={"username": CONFIG.username, "password": PASSWORD},
                name="/auth/login",
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    self.token = response.json().get("access_token")
                    return
                if response.status_code == 429 and attempt < LOGIN_ATTEMPTS - 1:
                    response.success()
                    time.sleep(1 + random.random())
                    continue
                response.failure(f"login {response.status_code}")
                return

    @task(5)
    def create_payment(self) -> None:
        if not self.token:
            return
        self.client.post(
            "/api/payments",
            json={"amount": "1.00", "currency": "EUR", "description": "loadtest (fictif)"},
            headers={"Authorization": f"Bearer {self.token}", "Idempotency-Key": f"lt-{uuid.uuid4()}"},
            name="/api/payments",
        )

    @task(1)
    def readiness(self) -> None:
        self.client.get("/api/health/ready", name="/api/health/ready")
