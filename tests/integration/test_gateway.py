"""Testes de integração do gateway.

Rodam apenas quando ``fastapi``/``faststream`` estão instalados. Usam o
``TestRedisBroker`` (broker Redis em memória) para exercitar o caminho completo
sem um servidor Redis real: WebSocket de entrada -> publicação -> worker
(simulado) -> ``agent_responses`` -> WebSocket de saída.
"""

import json

import pytest

pytest.importorskip("faststream")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient
from faststream.redis import TestRedisBroker

from src.core.config import get_settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.gateway.app import app, router

settings = get_settings()


@router.subscriber(settings.voice_commands_channel)
async def _echo_worker(command: VoiceCommand) -> None:
    """Worker simulado: devolve a resposta como o worker real faria."""
    await router.broker.publish(
        AgentResponse(
            session_id=command.session_id,
            reply_text=f"eco: {command.text}",
            audio_buffer_b64="QUJD",
        ),
        settings.agent_responses_channel,
    )


async def test_http_endpoints() -> None:
    async with TestRedisBroker(router.broker):
        with TestClient(app) as client:
            health = client.get("/health")
            assert health.status_code == 200
            assert health.json()["status"] == "ok"

            index = client.get("/")
            assert index.status_code == 200
            assert index.headers["content-type"].startswith("text/html")


async def test_ws_round_trip_delivers_agent_response() -> None:
    async with TestRedisBroker(router.broker):
        with TestClient(app) as client:
            with client.websocket_connect("/ws/sess-1") as ws:
                ws.send_text(json.dumps({"text": "olá"}))
                data = ws.receive_json()

    assert data["session_id"] == "sess-1"
    assert data["reply_text"] == "eco: olá"
    assert data["audio_buffer_b64"] == "QUJD"


async def test_empty_text_is_ignored() -> None:
    """Texto vazio é descartado; apenas o comando válido seguinte é respondido."""
    async with TestRedisBroker(router.broker):
        with TestClient(app) as client:
            with client.websocket_connect("/ws/sess-2") as ws:
                ws.send_text(json.dumps({"text": "   "}))
                ws.send_text(json.dumps({"text": "segundo"}))
                data = ws.receive_json()

    assert data["reply_text"] == "eco: segundo"
