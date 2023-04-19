from starlette.requests import Request

import settings
from app import exceptions

from .base import JSONResponse


async def handle_common(req: Request, exc: exceptions.BaseException) -> JSONResponse:
    msg = (
        "INTERNAL ERROR"
        if exc.http_status_code >= 500 and not settings.DEBUG
        else str(exc)
    )
    return JSONResponse({"error_message": msg}, status_code=exc.http_status_code)


async def handle_unknown(req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"error_message": "INTERNAL ERROR"}, status_code=500)


HANDLERS = {
    exceptions.BaseException: handle_common,
    Exception: handle_unknown,
}
