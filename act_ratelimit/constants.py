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
