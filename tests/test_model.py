from unittest.mock import patch

from app import extensions as exts
from app import models as m
from app import tasks

from .base import BaseTestCase


class TestCase(BaseTestCase):
    async def test_model(self):
        pass
