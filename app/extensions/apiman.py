from apiman.starlette import Extension
from elasticapm.contrib.asyncio.traces import async_capture_span

from app.base import ExtensionMixin, Starlette


class Apiman(Extension, ExtensionMixin):
    def _init_starlette_app(self, starlette: Starlette):
        self.init_app(starlette)

    async def async_validate_request(self, request, ignore=tuple()):
        async with async_capture_span(
            "VALIDATE request",
            span_type="serialization",
            span_subtype="request",
            span_action="validate data",
            leaf=True,
        ):
            return await super().async_validate_request(request, ignore)
