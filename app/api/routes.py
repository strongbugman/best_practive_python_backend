import typing

from starlette.routing import BaseRoute, Route

from .endpoints import healthiness

ROUTES: typing.List[BaseRoute] = [
    Route("/api/healthiness", healthiness.Healthiness),
]
