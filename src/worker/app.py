"""Composition root do worker FastStream."""

from faststream import FastStream
from faststream.redis import RedisBroker

from src.core.config import get_settings
from src.core.schemas import VoiceCommand
from src.worker.controller import WorkerController

settings = get_settings()
broker = RedisBroker(settings.redis_url)
app = FastStream(broker)
controller = WorkerController(settings, broker)


@app.on_startup
async def on_startup() -> None:
    await controller.startup()


@broker.subscriber(settings.voice_commands_channel)
async def handle_voice_command(command: VoiceCommand) -> None:
    await controller.handle_voice_command(command)
