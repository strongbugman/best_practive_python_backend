import asyncio
import collections
import functools
import inspect
import os
import typing

import betterproto
import grpclib
import sentry_sdk
from grpclib import events
from grpclib.server import Server as _GRPCServer
from grpclib.utils import graceful_exit
from oxalis.amqp import Oxalis as _Oxalis
from oxalis.amqp import Task
from starlette.applications import Starlette as _Starlette

from app.log import logger


class ExtensionMixin:
    def _init_starlette_app(self, _: "Starlette"):
        pass

    async def _on_startup(self):
        pass

    async def _on_shutdown(self):
        pass


class Starlette(_Starlette):
    """For API worker"""

    pass


class Oxalis(_Oxalis):
    """For distribute queue worker and client"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.event_handlers: typing.Dict[
            str, typing.List[typing.Callable]
        ] = collections.defaultdict(list)

    def add_init_handler(self, f: typing.Callable):
        self.event_handlers["init"].append(f)

    def add_close_handler(self, f: typing.Callable):
        self.event_handlers["close"].append(f)

    async def exec_task(self, task: Task, *task_args, **task_kwargs):
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("task_name", task.name)
            try:
                await super().exec_task(task, *task_args, **task_kwargs)
            except Exception as e:
                logger.exception(e)
                sentry_sdk.capture_exception(e)
            finally:
                pass

    def on_worker_init(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        for f in self.event_handlers["init"]:
            res = f()
            if inspect.iscoroutine(res):
                asyncio.get_event_loop().run_until_complete(res)

    def on_worker_close(self):
        for f in self.event_handlers["close"]:
            res = f()
            if inspect.iscoroutine(res):
                asyncio.get_event_loop().run_until_complete(res)


class GRPCServer(_GRPCServer):
    """For RPC worker"""

    def __init__(self, **kwargs) -> None:
        super().__init__([], **kwargs)
        self.event_handlers: typing.Dict[
            str, typing.List[typing.Callable]
        ] = collections.defaultdict(list)

    def __rpc_decorator(self, rpc: typing.Callable) -> typing.Callable:
        @functools.wraps(rpc)
        async def wrapper(*args, **kwargs):
            await rpc.__self__.before_request()
            await rpc(*args, **kwargs)
            await rpc.__self__.after_response()

        return wrapper

    def add_init_handler(self, f: typing.Callable):
        self.event_handlers["init"].append(f)

    def add_close_handler(self, f: typing.Callable):
        self.event_handlers["close"].append(f)

    def add_handlers(self, handlers: typing.List):
        for h in handlers:
            for route, handler in h.__mapping__().items():
                handler = grpclib.const.Handler(
                    self.__rpc_decorator(handler.func),
                    handler.cardinality,
                    handler.request_type,
                    handler.reply_type,
                )

                self._mapping[route] = handler

    async def _run(self, host, port):
        with graceful_exit([self]):
            await self.start(host=host, port=port)
            logger.info(f"Worker {os.getpid()} ({host}:{port}) start")
            await self.wait_closed()
            self.close

    def run_worker(self, host, port):
        self.on_worker_init()
        asyncio.get_event_loop().run_until_complete(self._run(host, port))
        self.on_worker_close()

    def on_worker_init(self):
        for f in self.event_handlers["init"]:
            res = f()
            if inspect.iscoroutine(res):
                asyncio.get_event_loop().run_until_complete(res)

    def on_worker_close(self):
        for f in self.event_handlers["close"]:
            res = f()
            if inspect.iscoroutine(res):
                asyncio.get_event_loop().run_until_complete(res)
