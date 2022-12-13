from __future__ import annotations

from redis.asyncio.client import Redis as _Redis
from elasticapm.contrib.asyncio.traces import async_capture_span

from app.base import ExtensionMixin


class Redis(_Redis, ExtensionMixin):
    async def execute_command(self, *args, **kw):
        async with async_capture_span(
            " ".join(args[:2]),
            span_type="db",
            span_subtype="redis",
            span_action="query",
            leaf=True,
            extra={
                "destination": {
                    "service": {"name": "", "resource": "redis", "type": ""},
                    "port": self.connection_pool.connection_kwargs.get("port", ""),
                    "address": self.connection_pool.connection_kwargs.get("host", ""),
                },
                "db": {
                    "statement": " ".join(
                        map(
                            lambda x: "<value>" if isinstance(x, bytes) else str(x),
                            args,
                        )
                    )
                },
            },
        ):
            return await super().execute_command(*args, **kw)

    async def _on_startup(self):
        await self.initialize()

    async def _on_shutdown(self):
        await self.close()
