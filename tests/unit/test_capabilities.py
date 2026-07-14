"""Testes do preflight de capacidades."""

from pathlib import Path

from src.core import capabilities as caps
from src.core.config import Settings


def _settings_with_voice(tmp_path: Path, *, with_config: bool) -> Settings:
    voice = tmp_path / "voz.onnx"
    voice.write_bytes(b"fake-onnx")
    if with_config:
        voice.with_suffix(voice.suffix + ".json").write_text("{}")
    return Settings(piper_voice_path=voice)


def test_ready_when_all_present(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(caps, "probe_ollama", lambda host, timeout=2.0: True)
    report = caps.resolve_capabilities(_settings_with_voice(tmp_path, with_config=True))
    assert report.ready is True


def test_not_ready_when_ollama_down(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(caps, "probe_ollama", lambda host, timeout=2.0: False)
    report = caps.resolve_capabilities(_settings_with_voice(tmp_path, with_config=True))
    assert report.ready is False
    assert report.voice_available is True


def test_not_ready_when_voice_config_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(caps, "probe_ollama", lambda host, timeout=2.0: True)
    report = caps.resolve_capabilities(
        _settings_with_voice(tmp_path, with_config=False)
    )
    assert report.voice_available is True
    assert report.voice_config_available is False
    assert report.ready is False


def test_describe_report_lists_all_capabilities(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(caps, "probe_ollama", lambda host, timeout=2.0: True)
    report = caps.resolve_capabilities(_settings_with_voice(tmp_path, with_config=True))
    lines = caps.describe_report(report)
    assert len(lines) == 3


def test_probe_ollama_returns_false_on_malformed_host() -> None:
    """Host sem esquema (ex.: "0.0.0.0") não deve derrubar o preflight."""
    assert caps.probe_ollama("0.0.0.0") is False
