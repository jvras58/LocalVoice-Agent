"""Testes da síntese de áudio (empacotamento WAV) sem depender do Piper real."""

import base64
import io
import wave
from pathlib import Path

import pytest

from src.tools.tts import PiperSynthesizer, load_piper_voice


class FakeVoice:
    """Voz falsa que escreve um WAV mono 16 bits determinístico."""

    def __init__(self, framerate: int = 22050) -> None:
        self._framerate = framerate

    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(self._framerate)
        wav_file.writeframes(b"\x00\x01" * max(len(text), 1))


def test_to_wav_bytes_produces_valid_wav() -> None:
    synth = PiperSynthesizer(FakeVoice())
    data = synth.to_wav_bytes("abc")

    assert data[:4] == b"RIFF"
    with wave.open(io.BytesIO(data), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050
        assert wav_file.getnframes() == 3


def test_to_wav_base64_matches_raw_bytes() -> None:
    synth = PiperSynthesizer(FakeVoice())
    text = "olá mundo"
    assert base64.b64decode(synth.to_wav_base64(text)) == synth.to_wav_bytes(text)


def test_load_piper_voice_missing_model(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_piper_voice(tmp_path / "inexistente.onnx")
