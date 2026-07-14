"""Síntese de voz local com Piper TTS.

A importação do pacote ``piper`` fica dentro de :func:`load_piper_voice` para que
o restante do sistema (e os testes) possa depender apenas do contrato estrutural
:class:`SynthesisVoice`, sem carregar o runtime ONNX.
"""

import base64
import io
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class SynthesisVoice(Protocol):
    """Contrato estrutural de uma voz do Piper capaz de escrever WAV."""

    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None:
        """Escreve o áudio sintetizado (com cabeçalho WAV) em ``wav_file``."""
        ...


@dataclass(frozen=True)
class PiperSynthesizer:
    """Sintetiza texto em áudio WAV usando uma :class:`SynthesisVoice` carregada."""

    voice: SynthesisVoice

    def to_wav_bytes(self, text: str) -> bytes:
        """Sintetiza ``text`` e devolve o conteúdo WAV completo em memória."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)
        return buffer.getvalue()

    def to_wav_base64(self, text: str) -> str:
        """Sintetiza ``text`` e devolve o WAV codificado em Base64 (ASCII)."""
        return base64.b64encode(self.to_wav_bytes(text)).decode("ascii")


def load_piper_voice(
    voice_path: Path,
    config_path: Path | None = None,
    *,
    use_cuda: bool = False,
) -> SynthesisVoice:
    """Carrega um modelo ``.onnx`` do Piper e retorna a voz pronta para uso.

    Levanta :class:`FileNotFoundError` com mensagem clara quando o modelo não
    existe, evitando erros obscuros vindos do runtime ONNX.
    """
    if not voice_path.is_file():
        raise FileNotFoundError(
            f"Modelo de voz do Piper não encontrado em: {voice_path}. "
            "Baixe uma voz (ver voices/README.md) ou ajuste "
            "a variável PIPER_VOICE_PATH."
        )

    from piper import PiperVoice

    config_arg = str(config_path) if config_path is not None else None
    return PiperVoice.load(str(voice_path), config_path=config_arg, use_cuda=use_cuda)
