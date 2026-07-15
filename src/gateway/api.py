"""Definição da superfície HTTP e WebSocket do gateway."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faststream.redis.fastapi import RedisRouter

from src.gateway.controller import GatewayController

_DEFAULT_CLIENT_DIR = Path(__file__).resolve().parents[2] / "client"


def create_api(
    controller: GatewayController,
    broker_router: RedisRouter,
    *,
    client_dir: Path = _DEFAULT_CLIENT_DIR,
) -> FastAPI:
    """Monta a aplicação FastAPI e conecta suas rotas ao controller."""
    api_router = APIRouter()

    @api_router.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(client_dir / "index.html")

    @api_router.get("/health")
    async def health() -> dict[str, object]:
        return controller.health()

    @api_router.websocket("/ws/{session_id}")
    async def voice_socket(websocket: WebSocket, session_id: str) -> None:
        await controller.handle_socket(websocket, session_id)

    app = FastAPI(title="LocalVoice Gateway")
    app.include_router(broker_router)
    app.include_router(api_router)
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
