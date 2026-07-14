"""Configuração central da aplicação, carregada de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parâmetros operacionais do LocalVoice.

    As variáveis usam o prefixo ``LOCALVOICE_`` (ex.: ``LOCALVOICE_OLLAMA_HOST``)
    e podem ser definidas em um arquivo ``.env`` na raiz do projeto. O prefixo
    evita colisão com variáveis de ferramentas — em especial ``OLLAMA_HOST``,
    usada pelo próprio Ollama para definir o endereço de escuta.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOCALVOICE_",
        extra="ignore",
    )

    # Message broker (Redis)
    redis_url: str = "redis://localhost:6379"
    voice_commands_channel: str = "voice_commands"
    agent_responses_channel: str = "agent_responses"

    # LLM local (Ollama)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Piper TTS
    piper_voice_path: Path = Field(default=Path("voices/pt_BR-faber-medium.onnx"))
    piper_config_path: Path | None = None
    piper_use_cuda: bool = False

    # Gateway HTTP/WebSocket
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000

    def resolved_piper_config_path(self) -> Path:
        """Descobre o ``.onnx.json`` da voz quando não é informado explicitamente."""
        if self.piper_config_path is not None:
            return self.piper_config_path
        return self.piper_voice_path.with_suffix(self.piper_voice_path.suffix + ".json")


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única de :class:`Settings` (cacheada)."""
    return Settings()
