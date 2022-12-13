#!/usr/bin/env python3
import asyncio
from contextlib import contextmanager
from functools import wraps

import click
import danio
import sentry_sdk
from IPython import embed
import uvicorn

import settings
from app import extensions

from app import applications
from app import tasks as _

sentry_sdk.init(**settings.SENTRY)
loop = asyncio.get_event_loop()

@contextmanager
def extension_life():
    loop.run_until_complete(extensions.start_extensions())
    yield
    loop.run_until_complete(extensions.stop_extensions())


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
