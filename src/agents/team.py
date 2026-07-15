"""Orquestração dos agentes especializados do LocalVoice."""

from agno.db.sqlite import SqliteDb
from agno.team import Team

from src.agents.conversation_agent import build_conversation_agent
from src.agents.factory import build_model
from src.agents.system_agent import build_system_agent
from src.core.config import Settings
from src.core.instructions import SHARED_INSTRUCTIONS, TEAM_LEADER_INSTRUCTIONS


def build_team(settings: Settings) -> Team:
    """Cria a equipe e mantém o histórico compartilhado por ``session_id``."""
    settings.agent_db_path.parent.mkdir(parents=True, exist_ok=True)

    return Team(
        id="localvoice-team",
        name="LocalVoice",
        model=build_model(settings),
        members=[
            build_conversation_agent(settings),
            build_system_agent(settings),
        ],
        db=SqliteDb(db_file=str(settings.agent_db_path)),
        instructions=[*SHARED_INSTRUCTIONS, *TEAM_LEADER_INSTRUCTIONS],
        add_history_to_context=True,
        num_history_runs=settings.agent_history_runs,
        markdown=False,
    )
