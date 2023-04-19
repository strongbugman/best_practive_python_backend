import sys

from loguru import logger

import settings

logger.add(
    sys.stdout,
    format="{time} {level} {message}",
    level="DEBUG" if settings.DEBUG else "INFO",
)
