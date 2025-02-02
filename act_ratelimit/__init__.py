# Copyright (c) 2025 syncblaze
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""A simple rate limiter for FastAPI."""



from math import ceil

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.websockets import WebSocket

from act_ratelimit.backends import BaseBackend
from act_ratelimit.constants import HTTP_CALLBACK_SIGNATURE
from act_ratelimit.constants import IDENTIFIER_SIGNATURE
from act_ratelimit.constants import WS_CALLBACK_SIGNATURE
from act_ratelimit.constants import RateLimitStrategy

__all__: tuple[str, ...] = ("ACTRatelimit",)


async def default_identifier(request: Request | WebSocket) -> str:
    ip = forwarded.split(",")[0] if (forwarded := request.headers.get("X-Forwarded-For")) else request.client.host
    return ip + ":" + request.scope["path"]


async def http_default_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """
    raise HTTPException(HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(pexpire)})


async def ws_default_callback(ws: WebSocket, pexpire: int):
    """
    default callback when too many requests
    :param ws:
    :param pexpire: The remaining milliseconds
    :return:
    """
    expire = ceil(pexpire / 1000)
    raise HTTPException(HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(expire)})


class ACTRatelimit:
    __slots__ = ()

    backend: BaseBackend | None = None
    prefix: str = "act-ratelimit"
    lua_sha: str | None = None
    identifier: IDENTIFIER_SIGNATURE = default_identifier
    http_callback: HTTP_CALLBACK_SIGNATURE = http_default_callback
    ws_callback: WS_CALLBACK_SIGNATURE = ws_default_callback
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW

    @classmethod
    async def init(
        cls,
        backend: BaseBackend,
        *,
        prefix: str | None = None,
        identifier: IDENTIFIER_SIGNATURE | None = None,
        http_callback: HTTP_CALLBACK_SIGNATURE | None = None,
        ws_callback: WS_CALLBACK_SIGNATURE | None = None,
        strategy: RateLimitStrategy | None = None,
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
        if strategy:
            cls.strategy = strategy

    @classmethod
    async def close(cls) -> None:
        await cls.backend.close()



__version__ = "0.0.1a2"