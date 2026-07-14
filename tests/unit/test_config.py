"""Testes da configuração central."""

from pathlib import Path

from src.core.config import Settings


def test_defaults() -> None:
    settings = Settings()
    assert settings.voice_commands_channel == "voice_commands"
    assert settings.agent_responses_channel == "agent_responses"


def test_config_path_inferred_from_voice_path() -> None:
    settings = Settings(piper_voice_path=Path("voices/pt_BR-faber-medium.onnx"))
    assert settings.resolved_piper_config_path() == Path(
        "voices/pt_BR-faber-medium.onnx.json"
    )


def test_explicit_config_path_is_preserved() -> None:
    explicit = Path("voices/custom.json")
    settings = Settings(
        piper_voice_path=Path("voices/voice.onnx"),
        piper_config_path=explicit,
    )
    assert settings.resolved_piper_config_path() == explicit


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "hermes3")
    settings = Settings()
    assert settings.ollama_model == "hermes3"
