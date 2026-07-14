"""Registro das conexões WebSocket ativas, indexadas por ``session_id``.

Depende apenas do contrato estrutural :class:`WebSocketLike`, o que mantém o
módulo testável sem subir um servidor FastAPI real.
"""

import asyncio
from typing import Any, Protocol


class WebSocketLike(Protocol):
    """Subconjunto da API de WebSocket usado pelo registro."""

    async def accept(self) -> None: ...

    async def send_json(self, data: Any) -> None: ...


class ConnectionRegistry:
    """Mapeia ``session_id`` para o WebSocket correspondente, de forma segura.

    Um :class:`asyncio.Lock` protege o dicionário contra conexões e desconexões
    concorrentes no mesmo event loop.
    """

    def __init__(self) -> None:
        self._connections: dict[str, WebSocketLike] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocketLike) -> None:
        """Aceita o WebSocket e o registra sob ``session_id``."""
        await websocket.accept()
        async with self._lock:
            self._connections[session_id] = websocket

    async def disconnect(self, session_id: str) -> None:
        """Remove o registro da sessão, se existir."""
        async with self._lock:
            self._connections.pop(session_id, None)

    async def send(self, session_id: str, payload: Any) -> bool:
        """Envia ``payload`` como JSON à sessão. Retorna ``False`` se ausente."""
        async with self._lock:
            websocket = self._connections.get(session_id)
        if websocket is None:
            return False
        await websocket.send_json(payload)
        return True

    def active_sessions(self) -> int:
        """Quantidade de sessões atualmente registradas."""
        return len(self._connections)
