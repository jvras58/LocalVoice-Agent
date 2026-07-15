"""Construção do modelo usado pelo assistente LocalVoice."""

from agno.models.ollama import Ollama

from src.core.config import Settings


def build_model(settings: Settings) -> Ollama:
    """Cria o modelo Ollama com geração estável para respostas faladas."""
    return Ollama(
        id=settings.ollama_model,
        host=settings.ollama_host,
        options={"temperature": settings.ollama_temperature},
    )
