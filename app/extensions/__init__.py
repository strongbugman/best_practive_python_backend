import settings

from .apiman import Apiman
from .cache import RedisCache, SizeLimitedMemoryCache
from .coroutine_pool import Pool
from .database import Database
from .jwt import Jwt
from .redis import Redis

read_database = Database(**settings.READ_DATABASE)
database = Database(**settings.DATABASE)
redis = Redis(**settings.REDIS)  # type: ignore
jwt = Jwt(**settings.JWT)  # type: ignore
memory_cache = SizeLimitedMemoryCache(settings.PROJECT_NAME)
redis_cache = RedisCache(settings.PROJECT_NAME, redis)
apiman = Apiman(**settings.APIMAN)
coroutine_pool = Pool(**settings.OXALIS_POOL)


EXTENSIONS = [
    redis,
    database,
    read_database,
    apiman,
    redis_cache,
    memory_cache,
]
_started = False


async def start_extensions():
    if _started:
        return
    for ext in EXTENSIONS:
        await ext._on_startup()


async def stop_extensions():
    if not _started:
        return
    for ext in EXTENSIONS:
        await ext._on_shutdown()
