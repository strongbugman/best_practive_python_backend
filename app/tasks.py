from app.applications import oxalis, oxalis_beater
from app.log import logger

register = oxalis.register(ack_always=True, reject=False)


@register
async def check():
    logger.info(f"Checking ")


oxalis_beater.register("*/1 * * * *", check)
