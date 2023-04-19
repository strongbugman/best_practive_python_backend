from apiman.starlette import Extension

from app.base import ExtensionMixin, Starlette


class Apiman(Extension, ExtensionMixin):
    def _init_starlette_app(self, starlette: Starlette):
        self.init_app(starlette)

    async def async_validate_request(self, request, ignore=tuple()):
        return await super().async_validate_request(request, ignore)
