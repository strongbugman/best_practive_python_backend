import asyncio

import sentry_sdk
from oxalis.pool import Pool as _Pool

from app.base import ExtensionMixin
from app.log import logger


class Pool(_Pool, ExtensionMixin):
    async def _on_shutdown(self):
        await self.wait_close()

    def check_future(self, f: asyncio.Future):
        e = f.exception()
        if e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
