"""Testes do registro de conexões WebSocket do gateway."""

from typing import Any

from src.gateway.connections import ConnectionRegistry


class FakeWebSocket:
    """WebSocket falso que atende ao contrato :class:`WebSocketLike`."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[Any] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Any) -> None:
        self.sent.append(data)


async def test_connect_accepts_and_registers() -> None:
    registry = ConnectionRegistry()
    ws = FakeWebSocket()
    await registry.connect("s1", ws)
    assert ws.accepted
    assert registry.active_sessions() == 1


async def test_send_delivers_to_registered_session() -> None:
    registry = ConnectionRegistry()
    ws = FakeWebSocket()
    await registry.connect("s1", ws)
    delivered = await registry.send("s1", {"reply_text": "oi"})
    assert delivered
    assert ws.sent == [{"reply_text": "oi"}]


async def test_send_to_unknown_session_returns_false() -> None:
    registry = ConnectionRegistry()
    assert await registry.send("ausente", {"x": 1}) is False


async def test_disconnect_removes_session() -> None:
    registry = ConnectionRegistry()
    ws = FakeWebSocket()
    await registry.connect("s1", ws)
    await registry.disconnect("s1")
    assert registry.active_sessions() == 0
    assert await registry.send("s1", {"x": 1}) is False
