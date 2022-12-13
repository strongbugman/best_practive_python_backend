from .. import base


class Healthiness(base.Endpoint):
    async def get(self, _: base.Request) -> base.Response:
        """
        summary: Test server health
        tags:
        - health
        responses:
          "200":
            description: OK
        """
        return base.Response()
