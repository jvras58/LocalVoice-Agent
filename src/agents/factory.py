"""Construtores dos objetos Agno (modelo e agentes).

Isola a criação de agentes da orquestração da equipe, permitindo reaproveitar
``build_model`` e ``make_agent`` conforme a equipe cresce.
"""

from agno.agent import Agent
from agno.models.ollama import Ollama

from src.core.config import Settings


def build_model(settings: Settings) -> Ollama:
    """Cria o modelo Ollama local a partir das configurações."""
    return Ollama(id=settings.ollama_model, host=settings.ollama_host)


def make_agent(
    settings: Settings,
    *,
    name: str,
    role: str,
    instructions: list[str],
    model: Ollama | None = None,
) -> Agent:
    """Cria um :class:`~agno.agent.Agent` configurado para saída falada.

    ``markdown=False`` mantém a resposta em texto puro, adequado ao TTS.
    """
    return Agent(
        name=name,
        role=role,
        model=model or build_model(settings),
        instructions=instructions,
        markdown=False,
    )
