"""Definição da superfície HTTP e WebSocket do gateway."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from faststream.redis.fastapi import RedisRouter

from src.gateway.controller import GatewayController
from src.gateway.routes import create_routes

_DEFAULT_CLIENT_DIR = Path(__file__).resolve().parents[2] / "client"


def create_api(
    controller: GatewayController,
    broker_router: RedisRouter,
    *,
    client_dir: Path = _DEFAULT_CLIENT_DIR,
) -> FastAPI:
    """Monta a aplicação, inclui os routers e serve os arquivos estáticos."""
    app = FastAPI(title="LocalVoice Gateway")
    app.include_router(broker_router)
    app.include_router(create_routes(controller, client_dir=client_dir))
    app.mount(
        "/css",
        StaticFiles(directory=client_dir / "css"),
        name="client-css",
    )
    app.mount(
        "/js",
        StaticFiles(directory=client_dir / "js"),
        name="client-js",
    )
    return app
