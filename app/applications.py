from aio_pika import RobustConnection
from yarl import URL
from oxalis.beater import Beater
from elasticapm.contrib.starlette import ElasticAPM

import settings
from app import extensions
from app.base import Starlette, Oxalis
from app.extensions.coroutine_pool import Pool
from app.api.routes import ROUTES
from app.api.exception_handlers import HANDLERS

oxalis = Oxalis(
    extensions.apm,
    RobustConnection(URL(settings.OXALIS_CONNECTION_URL)),
    pool=Pool(limit=-1, timeout=settings.OXALIS_POOL["timeout"]),
    **settings.OXALIS,
)
oxalis_beater = Beater(oxalis)
starlette = Starlette()
starlette.debug = settings.DEBUG
starlette.routes.extend(ROUTES)
for ext in extensions.EXTENSIONS:
    ext._init_starlette_app(starlette)
starlette.add_event_handler("startup", extensions.start_extensions)
starlette.add_event_handler("shutdown", extensions.stop_extensions)
starlette.add_event_handler("startup", oxalis.connect)
starlette.add_event_handler("shutdown", oxalis.disconnect)
for exc, handler in HANDLERS.items():
    starlette.add_exception_handler(exc, handler)
starlette.add_middleware(ElasticAPM, client=extensions.apm)
