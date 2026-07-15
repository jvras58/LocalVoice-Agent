"""API Gateway: WebSocket bidirecional entre cliente, Redis e worker."""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faststream.redis.fastapi import RedisRouter

from src.core.config import get_settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.gateway.connections import ConnectionRegistry

logger = logging.getLogger("localvoice.gateway")

settings = get_settings()
router = RedisRouter(settings.redis_url)
connections = ConnectionRegistry()

_CLIENT_DIR = Path(__file__).resolve().parents[2] / "client"
_CLIENT_INDEX = _CLIENT_DIR / "index.html"


@router.subscriber(settings.agent_responses_channel)
async def forward_response(response: AgentResponse) -> None:
    """Entrega a resposta ao WebSocket da sessão de origem."""
    delivered = await connections.send(response.session_id, response.model_dump())
    if not delivered:
        logger.warning(
            "Resposta sem WebSocket ativo para session_id=%s", response.session_id
        )


app = FastAPI(title="LocalVoice Gateway")
app.include_router(router)
app.mount("/css", StaticFiles(directory=_CLIENT_DIR / "css"), name="client-css")
app.mount("/js", StaticFiles(directory=_CLIENT_DIR / "js"), name="client-js")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve o cliente web mobile."""
    return FileResponse(_CLIENT_INDEX)


@app.get("/", include_in_schema=False)
async def health() -> dict[str, object]:
    """Checagem simples de liveness e sessões ativas."""
    return {"status": "ok", "active_sessions": connections.active_sessions()}


def _build_command(session_id: str, raw: str) -> VoiceCommand | None:
    """Converte JSON ou texto puro em um comando de voz válido."""
    text = raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and "text" in parsed:
        text = str(parsed["text"])

    text = text.strip()
    if not text:
        return None
    return VoiceCommand(session_id=session_id, text=text)


@app.websocket("/ws/{session_id}")
async def voice_socket(websocket: WebSocket, session_id: str) -> None:
    """Mantém a conexão de voz de uma sessão do cliente."""
    await connections.connect(session_id, websocket)
    logger.info("WebSocket conectado: session_id=%s", session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            command = _build_command(session_id, raw)
            if command is None:
                continue
            await router.broker.publish(command, settings.voice_commands_channel)
            logger.info("Comando publicado: session_id=%s", session_id)
    except WebSocketDisconnect:
        logger.info("WebSocket desconectado: session_id=%s", session_id)
    finally:
        await connections.disconnect(session_id)
