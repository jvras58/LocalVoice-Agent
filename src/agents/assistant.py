"""Construção do assistente LocalVoice com memória e ferramentas seguras."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from src.agents.factory import build_model
from src.core.config import Settings
from src.core.instructions import ASSISTANT_INSTRUCTIONS, SHARED_INSTRUCTIONS
from src.tools.assistant_tools import get_current_datetime, get_runtime_status


def build_assistant(settings: Settings) -> Agent:
    """Cria o agente principal, isolando o histórico por ``session_id``."""
    settings.agent_db_path.parent.mkdir(parents=True, exist_ok=True)

    return Agent(
        id="localvoice-assistant",
        name="LocalVoice",
        role="Atender solicitações por voz e executar ferramentas locais seguras.",
        model=build_model(settings),
        db=SqliteDb(db_file=str(settings.agent_db_path)),
        tools=[get_current_datetime, get_runtime_status],
        instructions=[*SHARED_INSTRUCTIONS, *ASSISTANT_INSTRUCTIONS],
        add_history_to_context=True,
        num_history_runs=settings.agent_history_runs,
        markdown=False,
    )
