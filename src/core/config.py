"""Configuração central da aplicação, carregada de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parâmetros operacionais do LocalVoice."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOCALVOICE_",
        extra="ignore",
    )

    redis_url: str = "redis://localhost:6379"
    voice_commands_channel: str = "voice_commands"
    agent_responses_channel: str = "agent_responses"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    database_url: str = "postgresql+psycopg://ai:ai@localhost:5532/ai"
    database_schema: str = "localvoice"
    session_table: str = "localvoice_sessions"
    agent_history_runs: int = Field(default=6, ge=1, le=20)

    piper_voice_path: Path = Field(default=Path("voices/pt_BR-faber-medium.onnx"))
    piper_config_path: Path | None = None
    piper_use_cuda: bool = False

    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000

    ssl_certfile: Path | None = Path("certs/localvoice.crt")
    ssl_keyfile: Path | None = Path("certs/localvoice.key")

    def resolved_piper_config_path(self) -> Path:
        """Descobre o ``.onnx.json`` quando o caminho não foi informado."""
        if self.piper_config_path is not None:
            return self.piper_config_path
        return self.piper_voice_path.with_suffix(self.piper_voice_path.suffix + ".json")

    def tls_files(self) -> tuple[Path, Path] | None:
        """Retorna o certificado e a chave quando ambos existem."""
        cert, key = self.ssl_certfile, self.ssl_keyfile
        if cert is not None and key is not None and cert.is_file() and key.is_file():
            return cert, key
        return None


@lru_cache
def get_settings() -> Settings:
    """Retorna a configuração cacheada da aplicação."""
    return Settings()
