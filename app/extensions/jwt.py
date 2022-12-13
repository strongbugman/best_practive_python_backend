import time
import typing

import jwt
from elasticapm.traces import capture_span
from starlette.responses import Response

from app.base import ExtensionMixin


class Jwt(ExtensionMixin):
    DecodeException = jwt.PyJWTError

    def __init__(self, secret: str):
        self.secret = secret

    def decode(self, token: str) -> typing.Dict[str, typing.Any]:
        with capture_span(
            "DECODE jwttoken",
            span_type="serialization",
            span_subtype="request",
            span_action="decode jwttoken",
            leaf=True,
        ):
            return jwt.decode(token, self.secret, algorithms=["HS256"])

    def encode(self, res: Response, key: str, data: typing.Dict, expire=24 * 60 * 60):
        with capture_span(
            "ENCODE jwttoken",
            span_type="serialization",
            span_subtype="response",
            span_action="encode jwttoken",
            leaf=True,
        ):
            data["exp"] = int(time.time()) + expire
            token = jwt.encode(data, self.secret)
            self.set_token(res, key, token)
