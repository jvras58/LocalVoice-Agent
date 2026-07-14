"""Testes da camada de agentes (executam apenas quando o Agno está instalado)."""

import pytest

pytest.importorskip("agno")

from src.agents.factory import build_model
from src.agents.team import build_team
from src.core.config import Settings


def test_build_model_uses_settings() -> None:
    settings = Settings(ollama_model="hermes3", ollama_host="http://host:1234")
    model = build_model(settings)
    assert model.id == "hermes3"
    assert model.host == "http://host:1234"


def test_build_team_has_single_member() -> None:
    team = build_team(Settings())
    assert len(team.members) == 1
    assert team.name == "LocalVoice"
