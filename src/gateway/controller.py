"""Casos de uso de transporte do gateway LocalVoice."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import WebSocket, WebSocketDisconnect

from src.core.config import Settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.gateway.connections import ConnectionRegistry

logger = logging.getLogger("localvoice.gateway")


class MessagePublisher(Protocol):
    """Contrato mínimo necessário para publicar comandos no broker."""

    async def publish(self, message: Any, channel: str) -> Any: ...


@dataclass(slots=True)
class GatewayController:
    """Coordena WebSockets, valida comandos e publica eventos no Redis."""

    settings: Settings
    publisher: MessagePublisher
    connections: ConnectionRegistry

    @staticmethod
    def build_command(session_id: str, raw: str) -> VoiceCommand | None:
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

    async def forward_response(self, response: AgentResponse) -> None:
        """Entrega uma resposta ao WebSocket da sessão de origem."""
        delivered = await self.connections.send(
            response.session_id,
            response.model_dump(),
        )
        if not delivered:
            logger.warning(
                "Resposta sem WebSocket ativo para session_id=%s",
                response.session_id,
            )

    async def handle_socket(self, websocket: WebSocket, session_id: str) -> None:
        """Mantém uma sessão WebSocket e publica os comandos recebidos."""
        await self.connections.connect(session_id, websocket)
        logger.info("WebSocket conectado: session_id=%s", session_id)
        try:
            while True:
                raw = await websocket.receive_text()
                command = self.build_command(session_id, raw)
                if command is None:
                    continue
                await self.publisher.publish(
                    command,
                    self.settings.voice_commands_channel,
                )
                logger.info("Comando publicado: session_id=%s", session_id)
        except WebSocketDisconnect:
            logger.info("WebSocket desconectado: session_id=%s", session_id)
        finally:
            await self.connections.disconnect(session_id)
