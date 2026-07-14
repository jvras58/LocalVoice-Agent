"""Montagem da equipe de agentes do LocalVoice.

Começa mínima (um assistente sob um líder), mas a estrutura de equipe já permite
adicionar novos membros e ferramentas sem alterar gateway ou worker.
"""

from agno.team import Team

from src.agents.factory import build_model, make_agent
from src.core.config import Settings
from src.core.instructions import (
    ASSISTANT_INSTRUCTIONS,
    SHARED_INSTRUCTIONS,
    TEAM_LEADER_INSTRUCTIONS,
)


def build_team(settings: Settings) -> Team:
    """Constrói a equipe Agno responsável por gerar a resposta falada."""
    assistant = make_agent(
        settings,
        name="Assistente",
        role="Responder às solicitações do usuário de forma útil e concisa.",
        instructions=[*SHARED_INSTRUCTIONS, *ASSISTANT_INSTRUCTIONS],
    )

    return Team(
        name="LocalVoice",
        model=build_model(settings),
        members=[assistant],
        instructions=[*SHARED_INSTRUCTIONS, *TEAM_LEADER_INSTRUCTIONS],
        markdown=False,
    )
