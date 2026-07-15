"""Testes da construção do assistente e do modelo Ollama."""

from pathlib import Path

import pytest

pytest.importorskip("agno")

from src.agents.assistant import build_assistant
from src.agents.factory import build_model
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


def test_build_assistant_has_memory_and_tools(tmp_path: Path) -> None:
    settings = Settings(agent_db_path=tmp_path / "sessions.db")
    assistant = build_assistant(settings)

    assert assistant.name == "LocalVoice"
    assert assistant.db is not None
    assert assistant.add_history_to_context is True
    assert len(assistant.tools) == 2
