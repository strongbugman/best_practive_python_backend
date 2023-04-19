import time
import typing

import jwt
from starlette.responses import Response

from app.base import ExtensionMixin


class Jwt(ExtensionMixin):
    DecodeException = jwt.PyJWTError

    def __init__(self, secret: str):
        self.secret = secret

    def decode(self, token: str) -> typing.Dict[str, typing.Any]:
        return jwt.decode(token, self.secret, algorithms=["HS256"])

    def encode(self, res: Response, key: str, data: typing.Dict, expire=24 * 60 * 60):
        data["exp"] = int(time.time()) + expire
        token = jwt.encode(data, self.secret)
        self.set_token(res, key, token)
