"""Testes da construção do assistente e do modelo Ollama."""

import pytest

pytest.importorskip("agno")

from agno.db.postgres import PostgresDb

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


def test_build_team_has_members_and_postgres_memory() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/test",
        database_schema="test_schema",
        session_table="test_sessions",
    )
    team = build_team(settings)

    assert team.name == "LocalVoice"
    assert isinstance(team.db, PostgresDb)
    assert team.db.db_url == settings.database_url
    assert team.db.db_schema == "test_schema"
    assert team.db.session_table_name == "test_sessions"
    assert team.add_history_to_context is True
    assert [member.name for member in team.members] == ["Conversação", "Sistema"]


def test_agents_have_separate_responsibilities() -> None:
    settings = Settings()
    conversation = build_conversation_agent(settings)
    system = build_system_agent(settings)

    assert not conversation.tools
    assert len(system.tools) == 2
