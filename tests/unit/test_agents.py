"""Testes da construção do assistente e do modelo Ollama."""

from pathlib import Path

import pytest

pytest.importorskip("agno")

from src.agents.conversation_agent import build_conversation_agent
from src.agents.factory import build_model
from src.agents.system_agent import build_system_agent
from src.agents.team import build_team
from src.core.config import Settings


def test_build_model_uses_settings() -> None:
    settings = Settings(
        ollama_model="hermes3",
        ollama_host="http://host:1234",
        ollama_temperature=0.25,
    )
    model = build_model(settings)
    assert model.id == "hermes3"
    assert model.host == "http://host:1234"
    assert model.options["temperature"] == 0.25


def test_build_team_has_members_and_memory(tmp_path: Path) -> None:
    settings = Settings(agent_db_path=tmp_path / "sessions.db")
    team = build_team(settings)

    assert team.name == "LocalVoice"
    assert team.db is not None
    assert team.add_history_to_context is True
    assert [member.name for member in team.members] == ["Conversação", "Sistema"]


def test_agents_have_separate_responsibilities() -> None:
    settings = Settings()
    conversation = build_conversation_agent(settings)
    system = build_system_agent(settings)

    assert not conversation.tools
    assert len(system.tools) == 2
