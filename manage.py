#!/usr/bin/env python3
import asyncio
from contextlib import contextmanager
from functools import wraps

import click
import danio
import sentry_sdk
import uvicorn
from IPython import embed

import settings
from app import applications, extensions
from app import tasks as _
from app.api.exception_handlers import HANDLERS as EXCEPTION_HANDLERS
from app.api.routes import ROUTES
from app.rpc import HANDLERS

sentry_sdk.init(**settings.SENTRY)
loop = asyncio.get_event_loop()

applications.starlette.routes.extend(ROUTES)
applications.starlette.debug = settings.DEBUG
for ext in extensions.EXTENSIONS:
    ext._init_starlette_app(applications.starlette)
applications.starlette.add_event_handler("startup", extensions.start_extensions)
applications.starlette.add_event_handler("shutdown", extensions.stop_extensions)
applications.starlette.add_event_handler("startup", applications.oxalis.connect)
applications.starlette.add_event_handler("shutdown", applications.oxalis.disconnect)
for exc, handler in EXCEPTION_HANDLERS.items():
    applications.starlette.add_exception_handler(exc, handler)

applications.oxalis.add_init_handler(extensions.start_extensions)
applications.oxalis.add_close_handler(extensions.stop_extensions)

applications.grpc_server.add_handlers(HANDLERS)
applications.grpc_server.add_init_handler(extensions.start_extensions)
applications.grpc_server.add_close_handler(extensions.stop_extensions)


@contextmanager
def extension_life():
    loop.run_until_complete(extensions.start_extensions())
    loop.run_until_complete(applications.oxalis.connect())
    yield
    loop.run_until_complete(extensions.stop_extensions())
    loop.run_until_complete(applications.oxalis.disconnect())


# commands
@click.group()
def main():
    pass


def cmd(func):
    wrapper = wraps(func)(click.command()(func))

    main.add_command(wrapper)

    return wrapper


@cmd
def shell():
    ctx = {"starlette": applications.starlette}
    with extension_life():
        embed(user_ns=ctx, using=lambda c: loop.run_until_complete(c), colors="neutral")


@cmd
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
def run_starlette(host, port):
    uvicorn.run(applications.starlette, host=host, port=port)


@cmd
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8080)
def run_grpc(host, port):
    applications.grpc_server.run_worker(host, port)


@cmd
def run_oxalis_worker():
    applications.oxalis.run_worker_master()


@cmd
def run_oxalis_beater():
    applications.oxalis_beater.run()


@cmd
def make_migrations():
    with extension_life():
        loop.run_until_complete(
            danio.manage.make_migration(
                extensions.database,
                danio.manage.get_models(["app.models"]),
                "./migrations",
            )
        )


if __name__ == "__main__":
    main()
