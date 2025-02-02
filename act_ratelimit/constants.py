import typing as t
from enum import IntEnum

from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

__all__: tuple[str, ...] = (
    "HTTP_CALLBACK_SIGNATURE",
    "IDENTIFIER_SIGNATURE",
    "WS_CALLBACK_SIGNATURE",
    "RateLimitStrategy",
)


class RateLimitStrategy(IntEnum):
    """
    Rate limit strategies.
    """

    FIXED_WINDOW = 0
    SLIDING_WINDOW = 1
    FIXED_WINDOW_ELASTIC = 2


HTTP_CALLBACK_SIGNATURE = t.Callable[[Request, Response, int], t.Awaitable[t.Any]]
IDENTIFIER_SIGNATURE = t.Callable[[Request | WebSocket], t.Awaitable[str]]
WS_CALLBACK_SIGNATURE = t.Callable[[WebSocket, int], t.Awaitable[t.Any]]
