from grpclib.testing import ChannelFor

from app.rpc import HANDLERS, healthiness
from app.rpc.proto.healthiness import HealthinessStub

from .base import BaseTestCase


class TestCase(BaseTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.channel_for = ChannelFor(HANDLERS)
        self.channel = await self.channel_for.__aenter__()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()
        await self.channel_for.__aexit__(None, None, None)

    async def test_rpc(self):
        stub = HealthinessStub(self.channel)
        res = await stub.check(healthiness.CheckRequest(message="hello"))
        assert res.message
