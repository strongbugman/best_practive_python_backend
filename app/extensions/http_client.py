import typing

from aiohttp import ClientResponse as Response
from aiohttp import ClientSession, ClientTimeout
from aiohttp.typedefs import StrOrURL

from app.base import ExtensionMixin


class Api(ExtensionMixin):
    session: ClientSession

    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs and isinstance(kwargs["timeout"], (int, float)):
            kwargs["timeout"] = ClientTimeout(total=kwargs["timeout"])
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        try:
            return f"{self.__class__.__name__}({self.session._base_url.host})"  # type: ignore
        except AttributeError:
            return self.__class__.__name__

    async def on_app_startup(self):
        self.session = ClientSession(*self.args, **self.kwargs)

    async def on_app_shutdown(self):
        return await self.session.close()

    async def request(self, method: str, url: StrOrURL, **kwargs) -> Response:
        name = url
        res = await self.session.request(method, url, **kwargs)
        await res.read()
        return res

    async def get(self, url: StrOrURL, **kwargs) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: StrOrURL, **kwargs) -> Response:
        return await self.request("POST", url, **kwargs)

    async def parse(self, response: Response) -> typing.Dict:
        return await response.json()
