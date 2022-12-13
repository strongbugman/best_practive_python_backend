import os
import typing
from contextlib import contextmanager

import sentry_sdk
import tenacity

from . import log


def retry():
    return tenacity.retry(
        stop=tenacity.stop.stop_after_attempt(3),
        wait=tenacity.wait.wait_random(min=1, max=2),
        reraise=True,
    )


@contextmanager
def suppress(capture: bool = True, exception: typing.Type[Exception] = Exception):
    try:
        yield
    except Exception as e:
        if os.environ.get("DEPLOY_ENV") == "test":
            raise
        if not isinstance(e, exception):
            raise
        elif capture:
            log.logger.exception(e)
            sentry_sdk.capture_exception(e)
