from app import tasks

from .base import BaseTestCase


class TestCase(BaseTestCase):
    async def test_hello(self):
        await tasks.check.delay()
