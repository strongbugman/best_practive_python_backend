from __future__ import annotations

from redis.asyncio.client import Redis as _Redis

from app.base import ExtensionMixin


class Redis(_Redis, ExtensionMixin):
    async def execute_command(self, *args, **kw):
        return await super().execute_command(*args, **kw)

    async def _on_startup(self):
        await self.initialize()

    async def _on_shutdown(self):
        await self.close()
