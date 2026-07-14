"""Testes dos contratos de mensageria."""

import pytest
from pydantic import ValidationError

from src.core.schemas import AgentResponse, VoiceCommand


def test_voice_command_roundtrip() -> None:
    command = VoiceCommand(session_id="s1", text="olá")
    restored = VoiceCommand.model_validate_json(command.model_dump_json())
    assert restored == command


def test_voice_command_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        VoiceCommand(session_id="s1", text="")


def test_agent_response_roundtrip() -> None:
    response = AgentResponse(session_id="s1", reply_text="oi", audio_buffer_b64="AAAA")
    restored = AgentResponse.model_validate_json(response.model_dump_json())
    assert restored == response
