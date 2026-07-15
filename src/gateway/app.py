"""Composition root do gateway FastAPI + FastStream."""

from faststream.redis.fastapi import RedisRouter

from src.core.config import get_settings
from src.gateway.api import create_api
from src.gateway.connections import ConnectionRegistry
from src.gateway.controller import GatewayController

settings = get_settings()
router = RedisRouter(settings.redis_url)
connections = ConnectionRegistry()
controller = GatewayController(settings, router.broker, connections)

router.subscriber(settings.agent_responses_channel)(controller.forward_response)

app = create_api(controller, router)
