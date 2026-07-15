"""Processamento dos comandos consumidos pelo worker LocalVoice."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from agno.team import Team

from src.agents.team import build_team
from src.core.capabilities import describe_report, resolve_capabilities
from src.core.config import Settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.core.speech_text import normalize_for_speech
from src.tools.tts import PiperSynthesizer, load_piper_voice

logger = logging.getLogger("localvoice.worker")


class MessagePublisher(Protocol):
    """Contrato mínimo necessário para publicar respostas no broker."""

    async def publish(self, message: Any, channel: str) -> Any: ...


@dataclass(slots=True)
class WorkerController:
    """Orquestra equipe, normalização, síntese e publicação da resposta."""

    settings: Settings
    publisher: MessagePublisher
    _team: Team | None = field(default=None, init=False, repr=False)
    _synthesizer: PiperSynthesizer | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def _get_team(self) -> Team:
        if self._team is None:
            self._team = build_team(self.settings)
        return self._team

    def _get_synthesizer(self) -> PiperSynthesizer:
        if self._synthesizer is None:
            voice = load_piper_voice(
                self.settings.piper_voice_path,
                self.settings.resolved_piper_config_path(),
                use_cuda=self.settings.piper_use_cuda,
            )
            self._synthesizer = PiperSynthesizer(voice)
        return self._synthesizer

    async def generate_reply(self, text: str, session_id: str) -> str:
        """Executa a equipe na sessão e normaliza o texto para exibição e TTS."""
        result = await self._get_team().arun(text, session_id=session_id)
        reply = normalize_for_speech(result.content)
        if reply:
            return reply
        return (
            "Não consegui formular uma resposta falada. "
            "Tente perguntar de outra forma."
        )

    async def startup(self) -> None:
        """Faz o preflight e aquece os recursos antes de consumir mensagens."""
        report = resolve_capabilities(self.settings)
        for line in describe_report(report):
            logger.info("Preflight: %s", line)
        if not report.ready:
            logger.warning(
                "Preflight incompleto — o worker pode falhar ao processar comandos."
            )

        self._get_team()
        self._get_synthesizer()
        logger.info("Worker pronto (modelo=%s).", self.settings.ollama_model)

    async def handle_voice_command(self, command: VoiceCommand) -> None:
        """Processa um comando e publica texto normalizado com áudio."""
        started = time.perf_counter()
        logger.info("Processando comando: session_id=%s", command.session_id)

        reply_text = await self.generate_reply(command.text, command.session_id)
        audio_b64 = await asyncio.to_thread(
            self._get_synthesizer().to_wav_base64,
            reply_text,
        )

        response = AgentResponse(
            session_id=command.session_id,
            reply_text=reply_text,
            audio_buffer_b64=audio_b64,
        )
        await self.publisher.publish(
            response,
            self.settings.agent_responses_channel,
        )

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Resposta publicada: session_id=%s duração=%.0fms",
            command.session_id,
            elapsed_ms,
        )
