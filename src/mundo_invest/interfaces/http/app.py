from fastapi import FastAPI

from mundo_invest.infrastructure.config import get_settings
from mundo_invest.interfaces.http.logging import (
    RequestIdMiddleware,
    configure_logging,
)
from mundo_invest.interfaces.http.routes import clientes, webhooks


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Mundo Invest Pipefy API")
    app.add_middleware(RequestIdMiddleware)
    app.include_router(clientes.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
