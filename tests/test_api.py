import asyncio

from async_asgi_testclient import TestClient

from app import extensions as exts
from app import models as m

from .base import BaseTestCase


class TestCase(BaseTestCase):
    async def test_openapi(self):
        exts.apiman.validate_specification()

    async def test_api(self):
        res = await self.api_client.get("/api/healthiness")
        assert res.status_code == 200
