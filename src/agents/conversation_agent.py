"""Agente especializado em conversação geral por voz."""

from agno.agent import Agent

from src.agents.factory import build_model
from src.core.config import Settings
from src.core.instructions import CONVERSATION_INSTRUCTIONS, SHARED_INSTRUCTIONS


def build_conversation_agent(settings: Settings) -> Agent:
    """Cria o membro responsável por respostas gerais em PT-BR."""
    return Agent(
        id="localvoice-conversation-agent",
        name="Conversação",
        role="Conversar, explicar e responder solicitações gerais do usuário.",
        model=build_model(settings),
        instructions=[*SHARED_INSTRUCTIONS, *CONVERSATION_INSTRUCTIONS],
        markdown=False,
    )
