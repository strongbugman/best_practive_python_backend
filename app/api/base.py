import asyncio
import functools
import time
import typing

import arrow
import orjson
import sentry_sdk
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.requests import Request as _Request
from starlette.responses import Response
from starlette.responses import Response as _Response
from starlette.types import Message

import settings
from app import exceptions, extensions
from app.extensions.apiman import Apiman
from app.extensions.jwt import Jwt


class Request(_Request):
    async def json(self) -> typing.Any:
        if not hasattr(self, "_json"):
            body = await self.body()
            self._json = orjson.loads(body)
        return self._json

    def get_token(self, key: str) -> str:
        return self.headers.get(f"x-{key}") or self.cookies.get(key) or ""


class Response(_Response):
    def set_token(self, key: str, token: str):
        self.set_cookie(
            key,
            token,
            httponly=True,
            samesite="lax",
            secure=self.secure,
        )
        self.headers[f"x-{key}"] = token


class JSONResponse(Response):
    media_type = "application/json"

    @staticmethod
    def _json_dump_default(value: typing.Any) -> typing.Any:
        if isinstance(value, arrow.Arrow):
            return value.datetime
        else:
            return value

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content, default=self._json_dump_default)


class Endpoint(HTTPEndpoint):
    async def validate(self, req: Request):
        await extensions.apiman.async_validate_request(req)

    async def on_request(self, req: Request):
        await self.validate(req)

    async def on_response(self, res: Response):
        pass

    async def method_not_allowed(self, request: Request) -> Response:
        raise HTTPException(status_code=405)

    async def get(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def head(self, req: Request) -> Response:
        return await self.get(req)

    async def post(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def patch(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def put(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def delete(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def options(self, req: Request) -> Response:
        raise HTTPException(status_code=405)

    async def dispatch(self) -> None:
        request = Request(self.scope, receive=self.receive)
        await self.on_request(request)
        # dispatch
        handler = getattr(self, request.method.lower(), self.method_not_allowed)
        is_async = asyncio.iscoroutinefunction(handler)

        if is_async:
            response = await handler(request)
        else:
            response = handler(request)
        await self.on_response(response)
        await response(self.scope, self.receive, self.send)


class JwtEndpoint(Endpoint):
    JWT_KEY: str = "jwttoken"
    JWT_EXPIRE: int = 24 * 60 * 60
    JWT_REFRESH_PERIOD: int = 12 * 60 * 60
    JWT_REQUIRED: bool = False
    jwt_force_refresh: bool = False
    jwt_data: typing.Dict[str, typing.Any] = {}
    _jwt_token: str = ""

    @property
    def authenticated(self) -> bool:
        return bool(self._jwt_token)

    async def on_request(self, req: Request):
        await super().on_request(req)
        try:
            self._jwt_token = req.get_token(self.JWT_KEY)
            self.jwt_data = extensions.jwt.decode(self._jwt_token)
        except self.jwt.DecodeException as e:
            if self.JWT_REQUIRED:
                raise e
            else:
                self.jwt_data = {}
                self._jwt_token = ""

    async def on_response(self, res: Response):
        await super().on_response(res)
        if self.jwt_data:
            if (
                self.jwt_force_refresh
                or "exp" not in self.jwt_data
                or not self._jwt_token
                or time.time() - (self.jwt_data["exp"] - self.JWT_EXPIRE)
                > self.JWT_REFRESH_PERIOD
            ):
                res.set_token(
                    self.JWT_KEY,
                    extensions.jwt.encode(self.jwt_data, expire=self.JWT_EXPIRE),
                )
            else:
                res.set_token(self.JWT_KEY, self._jwt_token)
