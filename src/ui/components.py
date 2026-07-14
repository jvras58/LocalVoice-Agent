"""Funções de apoio ao painel Streamlit.

O painel fala com o gateway pelo mesmo contrato do cliente mobile (WebSocket),
evitando acoplamento com detalhes internos do broker.
"""

import json
from urllib.parse import urlsplit

from websocket import create_connection

from src.core.schemas import AgentResponse


def build_ws_url(gateway_http_url: str, session_id: str) -> str:
    """Converte a URL HTTP do gateway na URL WebSocket da sessão."""
    parts = urlsplit(gateway_http_url)
    scheme = "wss" if parts.scheme == "https" else "ws"
    return f"{scheme}://{parts.netloc}/ws/{session_id}"


def send_command(
    gateway_http_url: str,
    session_id: str,
    text: str,
    timeout: float = 60.0,
) -> AgentResponse:
    """Envia ``text`` ao gateway e aguarda a :class:`AgentResponse` da sessão.

    Levanta :class:`TimeoutError` se nenhuma resposta chegar dentro de ``timeout``.
    """
    url = build_ws_url(gateway_http_url, session_id)
    connection = create_connection(url, timeout=timeout)
    try:
        connection.send(json.dumps({"text": text}))
        raw = connection.recv()
    finally:
        connection.close()
    return AgentResponse.model_validate_json(raw)
