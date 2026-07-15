"""Ferramentas locais e somente leitura disponíveis para o assistente."""

from datetime import datetime


def get_current_datetime() -> str:
    """Retorna a data, a hora e o fuso horário atuais da máquina local."""
    current = datetime.now().astimezone()
    return current.strftime("%d/%m/%Y %H:%M:%S %Z (UTC%z)")


def get_runtime_status() -> str:
    """Verifica a disponibilidade do Ollama e dos recursos locais do LocalVoice."""
    from src.core.capabilities import describe_report, resolve_capabilities
    from src.core.config import get_settings

    report = resolve_capabilities(get_settings())
    return "; ".join(describe_report(report))
