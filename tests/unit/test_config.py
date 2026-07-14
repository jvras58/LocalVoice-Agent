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


def test_env_prefix_override(monkeypatch) -> None:
    monkeypatch.setenv("LOCALVOICE_OLLAMA_MODEL", "hermes3")
    settings = Settings()
    assert settings.ollama_model == "hermes3"


def test_unprefixed_tool_env_is_ignored(monkeypatch) -> None:
    """Vars de ferramentas sem o prefixo (ex.: OLLAMA_HOST do Ollama) são ignoradas."""
    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0")
    settings = Settings()
    assert settings.ollama_host == "http://localhost:11434"


def test_tls_files_none_when_missing(tmp_path: Path) -> None:
    settings = Settings(
        ssl_certfile=tmp_path / "missing.crt",
        ssl_keyfile=tmp_path / "missing.key",
    )
    assert settings.tls_files() is None


def test_tls_files_returns_pair_when_present(tmp_path: Path) -> None:
    cert = tmp_path / "localvoice.crt"
    key = tmp_path / "localvoice.key"
    cert.write_text("cert")
    key.write_text("key")
    settings = Settings(ssl_certfile=cert, ssl_keyfile=key)
    assert settings.tls_files() == (cert, key)
