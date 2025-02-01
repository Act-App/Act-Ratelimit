"""A simple rate limiter for FastAPI."""

__version__ = "0.1"


from math import ceil
from typing import Any
from typing import Awaitable
from typing import Callable

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.websockets import WebSocket

from act_ratelimit.backends import BaseBackend

IDENTIFIER_SIGNATURE = Callable[[Request | WebSocket], Awaitable[str]]


async def default_identifier(request: Request | WebSocket) -> str:
    ip = forwarded.split(",")[0] if (forwarded := request.headers.get("X-Forwarded-For")) else request.client.host
    return ip + ":" + request.scope["path"]


HTTP_CALLBACK_SIGNATURE = Callable[[Request, Response, int], Awaitable[Any]]


async def http_default_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """
    expire = ceil(pexpire / 1000)
    raise HTTPException(HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(expire)})


WS_CALLBACK_SIGNATURE = Callable[[WebSocket, int], Awaitable[Any]]


async def ws_default_callback(ws: WebSocket, pexpire: int):
    """
    default callback when too many requests
    :param ws:
    :param pexpire: The remaining milliseconds
    :return:
    """
    expire = ceil(pexpire / 1000)
    raise HTTPException(HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(expire)})


class FastAPILimiter:
    __slots__ = ()

    backend: BaseBackend | None = None
    prefix: str = "act-ratelimit"
    lua_sha: str | None = None
    identifier: IDENTIFIER_SIGNATURE = default_identifier
    http_callback: HTTP_CALLBACK_SIGNATURE = http_default_callback
    ws_callback: WS_CALLBACK_SIGNATURE = ws_default_callback

    @classmethod
    async def init(
        cls,
        backend: BaseBackend,
        *,
        prefix: str | None = None,
        identifier: IDENTIFIER_SIGNATURE | None = None,
        http_callback: HTTP_CALLBACK_SIGNATURE | None = None,
        ws_callback: WS_CALLBACK_SIGNATURE | None = None,
    ) -> None:
        cls.backend = backend
        if prefix:
            cls.prefix = prefix
        if identifier:
            cls.identifier = identifier
        if http_callback:
            cls.http_callback = http_callback
        if ws_callback:
            cls.ws_callback = ws_callback

    @classmethod
    async def close(cls) -> None:
        await cls.backend.close()
