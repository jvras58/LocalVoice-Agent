"""Agente especializado em informações do ambiente LocalVoice."""

from agno.agent import Agent

from src.agents.factory import build_model
from src.core.config import Settings
from src.core.instructions import SHARED_INSTRUCTIONS, SYSTEM_INSTRUCTIONS
from src.tools.assistant_tools import get_current_datetime, get_runtime_status


def build_system_agent(settings: Settings) -> Agent:
    """Cria o membro com ferramentas locais seguras e somente leitura."""
    return Agent(
        id="localvoice-system-agent",
        name="Sistema",
        role="Consultar data, hora e estado dos recursos locais do LocalVoice.",
        model=build_model(settings),
        tools=[get_current_datetime, get_runtime_status],
        instructions=[*SHARED_INSTRUCTIONS, *SYSTEM_INSTRUCTIONS],
        markdown=False,
    )
