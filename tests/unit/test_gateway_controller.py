"""Testes dos casos de uso de transporte do gateway."""

from typing import Any

from src.core.config import Settings
from src.core.schemas import AgentResponse
from src.gateway.connections import ConnectionRegistry
from src.gateway.controller import GatewayController


class FakePublisher:
    async def publish(self, message: Any, channel: str) -> None:
        pass


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[Any] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Any) -> None:
        self.sent.append(data)


def make_controller() -> GatewayController:
    return GatewayController(
        Settings(),
        FakePublisher(),
        ConnectionRegistry(),
    )


def test_build_command_accepts_json_and_plain_text() -> None:
    controller = make_controller()

    json_command = controller.build_command("s1", '{"text": "olá"}')
    plain_command = controller.build_command("s2", "teste")

    assert json_command is not None
    assert json_command.model_dump() == {"session_id": "s1", "text": "olá"}
    assert plain_command is not None
    assert plain_command.model_dump() == {"session_id": "s2", "text": "teste"}


def test_build_command_rejects_empty_text() -> None:
    assert make_controller().build_command("s1", '{"text": "   "}') is None


async def test_forward_response_uses_connection_registry() -> None:
    controller = make_controller()
    websocket = FakeWebSocket()
    await controller.connections.connect("s1", websocket)

    await controller.forward_response(
        AgentResponse(
            session_id="s1",
            reply_text="oi",
            audio_buffer_b64="QUJD",
        )
    )

    assert websocket.sent == [
        {
            "session_id": "s1",
            "reply_text": "oi",
            "audio_buffer_b64": "QUJD",
        }
    ]
