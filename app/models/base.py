from __future__ import annotations

import csv
import dataclasses
import datetime
import enum
import io
import json
import os
import typing
from collections import defaultdict
from contextvars import ContextVar
from enum import Enum, IntEnum
from urllib.parse import quote

import arrow
import danio
import jinja2
from cached_property import cached_property

from app import extensions

TV = typing.TypeVar("TV")
BaseModelTV = typing.TypeVar("BaseModelTV", bound="BaseModel")


@dataclasses.dataclass(eq=False)
class ArrowField(danio.DateTimeField):
    """Import: timezone follow OS or settings config"""

    default: typing.Callable = lambda: arrow.Arrow.now()

    def to_database(self, value: typing.Any) -> str:
        if isinstance(value, arrow.Arrow):
            return value.format("YYYY-MM-DD HH:mm:ss")
        elif isinstance(value, str):
            return arrow.get(value).format("YYYY-MM-DD HH:mm:ss")
        elif isinstance(value, int):
            return arrow.Arrow.fromtimestamp(value).format("YYYY-MM-DD HH:mm:ss")
        else:
            return str(value)

    def to_python(self, value: typing.Any) -> typing.Any:
        if isinstance(value, datetime.datetime):
            return arrow.Arrow.fromdatetime(value)
        else:
            return value


class PickleMixin:
    def __getstate__(self):
        data = self.__dict__.copy()
        for key in self.__dict__:
            if isinstance(getattr(self.__class__, key, None), cached_property):
                data.pop(key)
            if key.startswith("cached_"):
                data.pop(key)
        return data

    def __setstate__(self, state: typing.Dict):
        self.__dict__.update(state)


@dataclasses.dataclass
class Model(danio.Model, PickleMixin):
    # mixins
    read_database: typing.ClassVar[danio.Database] = extensions.read_database
    write_database: typing.ClassVar[danio.Database] = extensions.database

    DATABASE_CONTEXT_VAR: typing.ClassVar[
        ContextVar[typing.Optional[danio.Database]]
    ] = ContextVar("database", default=None)

    id: typing.Annotated[int, danio.IntField(auto_increment=True, primary=True)] = 0
    created_at: typing.Annotated[arrow.Arrow, ArrowField] = dataclasses.field(
        default_factory=arrow.now
    )
    updated_at: typing.Annotated[arrow.Arrow, ArrowField] = dataclasses.field(
        default_factory=arrow.now
    )

    _table_abstracted: typing.ClassVar[bool] = True
    _table_name_snake_case: typing.ClassVar[bool] = True

    def __setstate__(self, state: typing.Dict):
        super().__setstate__(state)
        self.after_init()

    async def before_save(self):
        await super().before_save()
        self.updated_at = arrow.Arrow.now()

    @classmethod
    def get_database(
        cls, operation: danio.Operation, table: str, *args, **kwargs
    ) -> danio.Database:
        database = cls.DATABASE_CONTEXT_VAR.get()
        if not database:
            return (
                cls.read_database
                if operation == danio.Operation.READ
                else cls.write_database
            )
        else:
            return database
