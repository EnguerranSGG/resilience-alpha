from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api import routes
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.users import UserStore

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.service_name, settings.log_level, settings.log_file)

    app = FastAPI(
        title="RESILIENCE-ALPHA auth-service",
        version="0.1.0",
        description="Émission de JWT RS256 pour des comptes **fictifs** de laboratoire.",
    )
    app.state.settings = settings
    app.state.users = UserStore.from_spec(settings.users_spec)
    if not settings.private_key_pem or not len(app.state.users):
        logger.warning(
            "startup.secrets_missing",
            extra={"event": "startup.secrets_missing", "hint": "lancer scripts/generate-secrets.sh"},
        )
    app.include_router(routes.router)
    return app
