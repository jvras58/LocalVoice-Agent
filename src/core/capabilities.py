"""Preflight de capacidades: verifica dependências externas antes de operar.

Mantido leve (apenas biblioteca padrão) para poder rodar em qualquer processo
— gateway, worker ou CLI — sem custo de importação de bibliotecas pesadas.
"""

import urllib.request
from dataclasses import dataclass
from pathlib import Path

from src.core.config import Settings

_OLLAMA_PROBE_TIMEOUT_SECONDS = 2.0
_VALID_URL_SCHEMES = ("http://", "https://")


@dataclass(frozen=True)
class CapabilityReport:
    """Resultado do preflight das dependências externas."""

    ollama_host: str
    ollama_reachable: bool
    voice_path: Path
    voice_available: bool
    voice_config_path: Path
    voice_config_available: bool

    @property
    def ready(self) -> bool:
        """Indica se o sistema tem tudo o que precisa para responder por voz."""
        return (
            self.ollama_reachable
            and self.voice_available
            and self.voice_config_available
        )


def probe_ollama(host: str, timeout: float = _OLLAMA_PROBE_TIMEOUT_SECONDS) -> bool:
    """Retorna ``True`` se o endpoint ``/api/tags`` do Ollama responder 200.

    Um host sem esquema (ex.: ``"0.0.0.0"``) não é uma URL válida para conexão
    e é tratado como indisponível, em vez de derrubar o preflight.
    """
    if not host.startswith(_VALID_URL_SCHEMES):
        return False
    url = f"{host.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except OSError:  # URLError e TimeoutError são subclasses de OSError
        return False


def resolve_capabilities(settings: Settings) -> CapabilityReport:
    """Monta o :class:`CapabilityReport` a partir das configurações atuais."""
    config_path = settings.resolved_piper_config_path()
    return CapabilityReport(
        ollama_host=settings.ollama_host,
        ollama_reachable=probe_ollama(settings.ollama_host),
        voice_path=settings.piper_voice_path,
        voice_available=settings.piper_voice_path.is_file(),
        voice_config_path=config_path,
        voice_config_available=config_path.is_file(),
    )


def describe_report(report: CapabilityReport) -> list[str]:
    """Gera linhas legíveis descrevendo o estado de cada capacidade."""
    ok, fail = "OK", "FALTANDO"
    return [
        f"Ollama ({report.ollama_host}): {ok if report.ollama_reachable else fail}",
        f"Voz Piper ({report.voice_path}): {ok if report.voice_available else fail}",
        f"Config da voz ({report.voice_config_path}): "
        f"{ok if report.voice_config_available else fail}",
    ]
