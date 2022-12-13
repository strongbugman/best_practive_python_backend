from danio import Database as _Database

from app.base import ExtensionMixin


class Database(_Database, ExtensionMixin):
    async def _on_startup(self):
        await self.connect()

    async def _on_shutdown(self):
        await self.disconnect()
