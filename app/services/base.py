import typing


class Service:
    async def __call__(self, *args, **kwargs) -> typing.Any:
        pass
