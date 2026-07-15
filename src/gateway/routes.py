"""Rotas HTTP e WebSocket expostas pelo gateway."""

from pathlib import Path

from fastapi import APIRouter, WebSocket
from fastapi.responses import FileResponse

from src.gateway.controller import GatewayController


def create_routes(
    controller: GatewayController,
    *,
    client_dir: Path,
) -> APIRouter:
    """Cria as rotas e as conecta aos casos de uso do controller."""
    router = APIRouter()

    @router.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(client_dir / "index.html")

    @router.websocket("/ws/{session_id}")
    async def voice_socket(websocket: WebSocket, session_id: str) -> None:
        await controller.handle_socket(websocket, session_id)

    return router
