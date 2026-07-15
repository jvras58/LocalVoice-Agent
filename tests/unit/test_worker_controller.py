"""Testes da orquestração do worker sem Ollama ou Piper reais."""

from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("agno")

from src.core.config import Settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.worker.controller import WorkerController


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[tuple[Any, str]] = []

    async def publish(self, message: Any, channel: str) -> None:
        self.published.append((message, channel))


class FakeTeam:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[tuple[str, str]] = []

    async def arun(self, text: str, *, session_id: str) -> SimpleNamespace:
        self.calls.append((text, session_id))
        return SimpleNamespace(content=self.content)


class FakeSynthesizer:
    def to_wav_base64(self, text: str) -> str:
        assert "*" not in text
        return "QUJD"


def make_controller(
        content: str = "**Olá!**") -> tuple[WorkerController, FakePublisher]:
    publisher = FakePublisher()
    controller = WorkerController(Settings(), publisher)
    controller._team = FakeTeam(content)
    controller._synthesizer = FakeSynthesizer() 
    return controller, publisher


async def test_generate_reply_preserves_session_and_normalizes_output() -> None:
    controller, _ = make_controller()

    reply = await controller.generate_reply("oi", "sess-1")

    assert reply == "Olá!"
    assert controller._team is not None
    assert controller._team.calls == [("oi", "sess-1")]


async def test_handle_voice_command_publishes_agent_response() -> None:
    controller, publisher = make_controller("Resposta *limpa*")

    await controller.handle_voice_command(
        VoiceCommand(session_id="sess-2", text="teste")
    )

    assert len(publisher.published) == 1
    response, channel = publisher.published[0]
    assert isinstance(response, AgentResponse)
    assert response.reply_text == "Resposta limpa"
    assert response.audio_buffer_b64 == "QUJD"
    assert channel == controller.settings.agent_responses_channel
