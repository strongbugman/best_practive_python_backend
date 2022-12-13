import asyncio

import elasticapm
import elasticapm.conf.constants
import elasticapm.instrumentation.control
import sentry_sdk
from elasticapm.base import Client as APMClient
from oxalis.amqp import Oxalis as _Oxalis
from oxalis.amqp import Task
from starlette.applications import Starlette as _Starlette

from app.log import logger
from app import extensions


class ExtensionMixin:
    def _init_starlette_app(self, _: "Starlette"):
        pass

    async def _on_startup(self):
        pass

    async def _on_shutdown(self):
        pass


class Starlette(_Starlette):
    """For API worker"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = False

    async def startup(self):
        if not self.started:
            await self.router.startup()
            self.started = True

    async def shutdown(self):
        if self.started:
            await self.router.shutdown()
            self.started = False


class Oxalis(_Oxalis):
    """For distribute queue worker and client"""

    def __init__(self, apm: APMClient, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.apm = apm

    async def exec_task(self, task: Task, *task_args, **task_kwargs):
        self.apm.begin_transaction("task")
        elasticapm.set_transaction_name(task.name)
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("task_name", task.name)
            try:
                await super().exec_task(task, *task_args, **task_kwargs)
                elasticapm.set_transaction_result("Succeed")
                elasticapm.set_transaction_outcome(
                    elasticapm.conf.constants.OUTCOME.SUCCESS, override=False
                )
            except Exception as e:
                logger.exception(e)
                sentry_sdk.capture_exception(e)
                self.apm.capture_exception()
                elasticapm.set_transaction_result("Failed")
                elasticapm.set_transaction_outcome(
                    elasticapm.conf.constants.OUTCOME.FAILURE, override=False
                )
            finally:
                self.apm.end_transaction()

    def on_worker_init(self):
        elasticapm.instrumentation.control.instrument()
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(extensions.start_extensions())

    def on_worker_close(self):
        asyncio.get_event_loop().run_until_complete(extensions.stop_extensions())
        self.apm.close()
