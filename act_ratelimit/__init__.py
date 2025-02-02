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

from fastapi import HTTPException
from fastapi import WebSocketException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.status import WS_1013_TRY_AGAIN_LATER
from starlette.websockets import WebSocket

from act_ratelimit.backends import BaseBackend
from act_ratelimit.constants import HTTP_CALLBACK_SIGNATURE
from act_ratelimit.constants import IDENTIFIER_SIGNATURE
from act_ratelimit.constants import WS_CALLBACK_SIGNATURE
from act_ratelimit.constants import RateLimitStrategy

__all__: tuple[str, ...] = ("ACTRatelimit",)


async def default_identifier(request: Request | WebSocket) -> str:
    """default identifier function

    Args:
        request: The Request or WebSocket object.

    Returns:
        The identifier.
    """
    ip = forwarded.split(",")[0] if (forwarded := request.headers.get("X-Forwarded-For")) else request.client.host
    return ip + ":" + request.scope["path"]


async def http_default_callback(request: Request, response: Response, pexpire: int):
    """default callback when too many requests

    Args:
        request: The Request object.
        response: The Response object.
        pexpire: The remaining milliseconds.
    """
    raise HTTPException(HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(pexpire)})


async def ws_default_callback(ws: WebSocket, pexpire: int):
    """default callback when too many messages

    Args:
        ws: The WebSocket connection.
        pexpire: The remaining milliseconds.
    """
    raise WebSocketException(code=WS_1013_TRY_AGAIN_LATER, reason=f"Too Many Messages. Retry-After: {pexpire}")


class ACTRatelimit:
    __slots__ = ()

    backend: BaseBackend | None = None
    prefix: str = "act-ratelimit"
    lua_sha: str | None = None
    identifier: IDENTIFIER_SIGNATURE = default_identifier
    http_callback: HTTP_CALLBACK_SIGNATURE = http_default_callback
    ws_callback: WS_CALLBACK_SIGNATURE = ws_default_callback
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    disabled: bool = False

    @classmethod
    async def init(
        cls,
        backend: BaseBackend,
        *,
        prefix: str = "act-ratelimit",
        identifier: IDENTIFIER_SIGNATURE = default_identifier,
        http_callback: HTTP_CALLBACK_SIGNATURE = http_default_callback,
        ws_callback: WS_CALLBACK_SIGNATURE = ws_default_callback,
        strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
        disabled: bool = False,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            backend: The backend to use.
            prefix: The prefix to use for the keys. Defaults to "act-ratelimit".
            identifier: The function to use to get the identifier. Defaults to the IP address.
            http_callback: The callback to use when the ratelimit is hit for HTTP requests. Defaults to a 429 error.
            ws_callback: The callback to use when the ratelimit is hit for WebSocket messages. Defaults to a 1013 error.
            strategy: The strategy to use. Defaults to RateLimitStrategy.FIXED_WINDOW.
            disabled: Whether to disable the rate limiter. Defaults to False.
        """
        cls.backend = backend
        cls.prefix = prefix
        cls.identifier = identifier
        cls.http_callback = http_callback
        cls.ws_callback = ws_callback
        cls.strategy = strategy
        cls.disabled = disabled

    @classmethod
    async def close(cls) -> None:
        await cls.backend.close()


__version__ = "0.0.1a2"
