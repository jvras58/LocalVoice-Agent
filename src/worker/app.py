"""Worker Agno + Piper: consome comandos, executa o agente e sintetiza áudio."""

import asyncio
import logging
import time

from agno.team import Team
from faststream import FastStream
from faststream.redis import RedisBroker

from src.agents.team import build_team
from src.core.capabilities import describe_report, resolve_capabilities
from src.core.config import get_settings
from src.core.schemas import AgentResponse, VoiceCommand
from src.core.speech_text import normalize_for_speech
from src.tools.tts import PiperSynthesizer, load_piper_voice

logger = logging.getLogger("localvoice.worker")

settings = get_settings()
broker = RedisBroker(settings.redis_url)
app = FastStream(broker)

_team: Team | None = None
_synthesizer: PiperSynthesizer | None = None


def _get_team() -> Team:
    global _team
    if _team is None:
        _team = build_team(settings)
    return _team


def _get_synthesizer() -> PiperSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        voice = load_piper_voice(
            settings.piper_voice_path,
            settings.resolved_piper_config_path(),
            use_cuda=settings.piper_use_cuda,
        )
        _synthesizer = PiperSynthesizer(voice)
    return _synthesizer


async def _generate_reply(text: str, session_id: str) -> str:
    """Executa o agente na sessão e devolve texto seguro para exibição e TTS."""
    result = await _get_team().arun(text, session_id=session_id)
    reply = normalize_for_speech(result.content)
    if reply:
        return reply
    return "Não consegui formular uma resposta falada. Tente perguntar de outra forma."


@app.on_startup
async def on_startup() -> None:
    """Inicializa recursos pesados e registra o preflight de capacidades."""
    report = resolve_capabilities(settings)
    for line in describe_report(report):
        logger.info("Preflight: %s", line)
    if not report.ready:
        logger.warning(
            "Preflight incompleto — o worker pode falhar ao processar comandos."
        )
    _get_team()
    _get_synthesizer()
    logger.info("Worker pronto (modelo=%s).", settings.ollama_model)


@broker.subscriber(settings.voice_commands_channel)
async def handle_voice_command(command: VoiceCommand) -> None:
    """Processa um comando e publica texto normalizado com áudio sintetizado."""
    started = time.perf_counter()
    logger.info("Processando comando: session_id=%s", command.session_id)

    reply_text = await _generate_reply(command.text, command.session_id)
    audio_b64 = await asyncio.to_thread(_get_synthesizer().to_wav_base64, reply_text)

    response = AgentResponse(
        session_id=command.session_id,
        reply_text=reply_text,
        audio_buffer_b64=audio_b64,
    )
    await broker.publish(response, settings.agent_responses_channel)

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "Resposta publicada: session_id=%s duração=%.0fms",
        command.session_id,
        elapsed_ms,
    )
