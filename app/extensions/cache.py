import abc
import functools
import inspect
import pickle
import sys
import time
import typing
from collections import OrderedDict
from contextlib import suppress

from app.base import ExtensionMixin
from app.log import logger

from .redis import Redis


class CacheExpireException(Exception):
    pass


class BaseCache(abc.ABC, ExtensionMixin):
    def __init__(self, key_prefix: str, **options) -> None:
        self.key_prefix = key_prefix

    @abc.abstractmethod
    async def _set(self, key: str, ttl: int, data: bytes):
        pass

    @abc.abstractmethod
    async def _get(self, key: str) -> bytes:
        pass

    @abc.abstractmethod
    async def clear(self):
        pass

    @abc.abstractmethod
    async def delete(self, key: str):
        pass

    async def set(self, key: str, obj: typing.Any, ttl: int):
        await self._set(f"{self.key_prefix}_{key}", ttl, pickle.dumps(obj))

    async def get(self, key: str, default=None) -> typing.Any:
        try:
            return pickle.loads(await self._get(f"{self.key_prefix}_{key}"))
        except CacheExpireException:
            return default

    def generate_cache_key(
        self, __prefix: str, __func: typing.Callable, *args, **kwargs
    ) -> str:
        appends = [__func.__qualname__]
        for _, a in enumerate(args):
            if inspect.isclass(a):
                a = a.__name__
            appends.append(str(a))
        for k, v in sorted(kwargs.items(), key=lambda item: item[0]):
            if k == "force_update":
                continue
            appends.append(str(v))
        return f"{__prefix}_{'_'.join(appends)}"

    def cached(self, ttl: int, nullable=False, key_prefix="") -> typing.Callable:
        def decoretor(func: typing.Callable) -> typing.Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> typing.Any:
                cache_key = self.generate_cache_key(key_prefix, func, *args, **kwargs)
                result = (
                    None
                    if kwargs.get("force_update", False)
                    else await self.get(cache_key, None)
                )
                if result is None:
                    if (
                        not getattr(func, "__cached_wrapper__", False)
                        and "force_update" in kwargs
                    ):
                        kwargs.pop("force_update")
                    result = func(*args, **kwargs)
                    if inspect.iscoroutine(result):
                        result = await result
                    if result or nullable:
                        await self.set(cache_key, result, ttl)
                return result

            setattr(wrapper, "__cached_wrapper__", True)
            return wrapper

        return decoretor


class MemoryCache(BaseCache):
    """LRU memory cache"""

    def __init__(
        self, key_prefix: str, max_count=300, cull_count=100, **options
    ) -> None:
        self.max_count = max_count
        self.cull_count = cull_count
        self.data: typing.OrderedDict[
            str, typing.Tuple[float, int, bytes]
        ] = OrderedDict()
        super().__init__(key_prefix, **options)

    async def clear(self):
        self.data.clear()

    def _on_pop(self, key: str, time: float, ttl: int, data: bytes):
        pass

    async def delete(self, key: str):
        with suppress(KeyError):
            self._on_pop(key, *self.data.pop(key))

    async def _get(self, key: str) -> bytes:
        try:
            created_at, ttl, data = self.data[key]
            if (created_at + ttl) >= time.time():
                self.data.move_to_end(key, last=False)
                return data
            else:
                self._on_pop(key, *self.data.pop(key))
                raise CacheExpireException("Expired")
        except KeyError as e:
            raise CacheExpireException("Not found") from e

    async def _set(self, key: str, ttl: int, data: bytes):
        if len(self.data) >= self.max_count:
            logger.warning(f"clean mem cache {self.max_count}")
            for _ in range(self.cull_count):
                self.data.popitem()

        self.data[key] = (time.time(), ttl, data)


class SizeLimitedMemoryCache(MemoryCache):
    """Limit by memory size"""

    def __init__(
        self,
        key_prefix: str,
        cull_rate=0.3,
        max_size=128 * 1024 * 1024,
        **options,
    ) -> None:
        super().__init__(key_prefix, **options)
        self.cull_rate = cull_rate
        self.max_size = max_size
        self.size = 0
        self.ts_size = sys.getsizeof(time.time())

    def _on_pop(self, key: str, time: float, ttl: int, data: bytes):
        self.size -= sys.getsizeof(key.encode())
        self.size -= sys.getsizeof(ttl)
        self.size -= sys.getsizeof(data)
        self.size -= self.ts_size

    async def _set(self, key: str, ttl: int, data: bytes):
        if self.size >= self.max_size:
            logger.warning(f"clean mem cache {self.size}")
            while self.data and self.size >= self.max_size * (1 - self.cull_rate):
                _k, (_t, _ttl, _data) = self.data.popitem()
                self._on_pop(_k, _t, _ttl, _data)

        self.data[key] = (time.time(), ttl, data)
        self.size += sys.getsizeof(key.encode())
        self.size += sys.getsizeof(ttl)
        self.size += sys.getsizeof(data)
        self.size += self.ts_size


class RedisCache(BaseCache):
    def __init__(self, key_prefix: str, redis: Redis, **options) -> None:
        self.redis = redis
        super().__init__(key_prefix, **options)

    async def clear(self):
        await self.redis.flushdb()

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def _get(self, key: str) -> bytes:
        data = await self.redis.get(key)
        if not data:
            raise CacheExpireException("Not found or expired")

        return data

    async def _set(self, key: str, ttl: int, data: bytes):
        await self.redis.set(key, data, ex=ttl)
