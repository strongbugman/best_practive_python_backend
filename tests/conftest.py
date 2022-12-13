import asyncio
import os

import pytest


def pytest_configure():
    os.environ["ENVIRONMENT"] = "test"
    os.environ["PROJECT_NAME"] = "test_app"


@pytest.fixture()
def event_loop():
    """Make sure all test case using same loop"""
    yield asyncio.get_event_loop()
