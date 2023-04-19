from async_asgi_testclient import TestClient

from app import applications
from app import extensions as exts

from .base import BaseTestCase


class TestCase(BaseTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.api_client = TestClient(applications.starlette)

    async def test_openapi(self):
        exts.apiman.validate_specification()

    async def test_api(self):
        res = await self.api_client.get("/api/healthiness")
        assert res.status_code == 200
