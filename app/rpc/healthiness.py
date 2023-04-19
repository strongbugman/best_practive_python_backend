from app.log import logger

from .base import EventMixin
from .proto.healthiness import CheckRequest, CheckResponse, HealthinessBase


class Healthiness(HealthinessBase, EventMixin):
    async def before_request(self):
        logger.info("before health check")

    async def after_response(self):
        logger.info("after health check")

    async def check(self, check_request: "CheckRequest") -> "CheckResponse":
        return CheckResponse(message=f"OK(-{check_request.message})")
