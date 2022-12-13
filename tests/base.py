import unittest
import inspect
import asyncio

import danio
from async_asgi_testclient import TestClient

import settings
from app import extensions, applications


class BaseTestCase(unittest.TestCase):
    def _callSetUp(self):
        self.setUp()
        self._callAsync(self.asyncSetUp)

    def _callTestMethod(self, method):
        self._callAsync(method)

    def _callTearDown(self):
        self._callAsync(self.asyncTearDown)
        self.tearDown()

    def _callCleanup(self, function, *args, **kwargs):
        self._callAsync(function, *args, **kwargs)

    def _callAsync(self, func, /, *args, **kwargs):
        ret = func(*args, **kwargs)
        if inspect.isawaitable(ret):
            return asyncio.get_event_loop().run_until_complete(ret)
        else:
            return ret

    async def asyncSetUp(self) -> None:
        await extensions.start_extensions()

        self.api_client = TestClient(applications.starlette)


        for c in (extensions.memory_cache, extensions.redis_cache):
            await c.clear()
        await extensions.redis.flushdb()
        await extensions.database.execute(f"DROP DATABASE IF EXISTS {settings.PROJECT_NAME}")
        await extensions.database.execute(
            f"CREATE DATABASE IF NOT EXISTS `{settings.PROJECT_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        await extensions.database.execute(f"USE `{settings.PROJECT_NAME}`;")
        await extensions.read_database.execute(f"USE `{settings.PROJECT_NAME}`;")
        for m in danio.manage.get_models(["app.models"]):
            await extensions.database.execute(m.schema.to_sql())

    async def asyncTearDown(self) -> None:
        await extensions.stop_extensions()
