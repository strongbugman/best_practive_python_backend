from aio_pika import RobustConnection
from oxalis.beater import Beater
from yarl import URL

import settings
from app.base import GRPCServer, Oxalis, Starlette
from app.extensions.coroutine_pool import Pool

oxalis = Oxalis(
    RobustConnection(URL(settings.OXALIS_CONNECTION_URL)),
    pool=Pool(limit=-1, timeout=settings.OXALIS_POOL["timeout"]),
    **settings.OXALIS,
)
oxalis_beater = Beater(oxalis)

starlette = Starlette()

grpc_server = GRPCServer()
