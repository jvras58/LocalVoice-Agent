"""Contratos de mensageria trocados entre gateway e worker via Redis."""

from pydantic import BaseModel, Field


class VoiceCommand(BaseModel):
    """Comando de voz transcrito no cliente e publicado em ``voice_commands``."""

    session_id: str = Field(..., description="Identificador da sessão/WebSocket")
    text: str = Field(..., min_length=1, description="Texto transcrito do áudio")


class AgentResponse(BaseModel):
    """Resposta do agente publicada em ``agent_responses``.

    Carrega o texto final e o áudio sintetizado pelo Piper já codificado em
    Base64, pronto para ser reproduzido pelo cliente.
    """

    session_id: str = Field(..., description="Identificador da sessão de origem")
    reply_text: str = Field(..., description="Resposta textual final do agente")
    audio_buffer_b64: str = Field(
        ..., description="Buffer de áudio WAV em Base64 gerado pelo Piper"
    )
