from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from act_ratelimit import ACTRatelimit
from act_ratelimit.constants import HTTP_CALLBACK_SIGNATURE
from act_ratelimit.constants import IDENTIFIER_SIGNATURE
from act_ratelimit.constants import WS_CALLBACK_SIGNATURE
from act_ratelimit.constants import RateLimitStrategy

__all__: tuple[str, ...] = ("RateLimiter", "WebSocketRateLimiter")


class RateLimiter:
    def __init__(
        self,
        *,
        times: int = 1,
        milliseconds: int = 0,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        identifier: IDENTIFIER_SIGNATURE | None = None,
        callback: HTTP_CALLBACK_SIGNATURE | None = None,
        strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
    ):
        self.times = times
        assert self.times >= 0, "times must be greater than or equal to 0"
        self.milliseconds = milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        assert self.milliseconds >= 0, "time must be greater than or equal to 0"
        self.identifier = identifier
        self.callback = callback
        self.strategy = strategy

        self.route_index = 0
        self.dep_index = 0

    def _set_indexes(self, request: Request):
        for i, route in enumerate(request.app.routes):
            if not isinstance(route, APIRoute):
                continue
            if route.path == request.scope["path"] and request.method in route.methods:
                self.route_index = i
                for j, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:  # type: ignore
                        self.dep_index = j
                        break

    async def __call__(self, request: Request, response: Response):
        assert ACTRatelimit.backend is not None, "You must call FastAPILimiter.init in startup event of fastapi!"
        if self.milliseconds == 0:
            return

        self._set_indexes(request)

        # moved here because constructor run before app startup
        identifier = self.identifier or ACTRatelimit.identifier
        strategy = self.strategy or ACTRatelimit.strategy
        rate_key = await identifier(request)
        key = f"{ACTRatelimit.prefix}:{rate_key}:{self.route_index}:{self.dep_index}"
        print(key)
        pexpire = await ACTRatelimit.backend.check(key, self.times, self.milliseconds, strategy)
        if pexpire != 0:
            callback = self.callback or ACTRatelimit.http_callback
            return await callback(request, response, pexpire)


class WebSocketRateLimiter:
    def __init__(
        self,
        *,
        times: int = 1,
        milliseconds: int = 0,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        identifier: IDENTIFIER_SIGNATURE | None = None,
        callback: WS_CALLBACK_SIGNATURE | None = None,
        strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
    ):
        self.times = times
        assert self.times >= 0, "times must be greater than or equal to 0"
        self.milliseconds = milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        assert self.milliseconds >= 0, "time must be greater than or equal to 0"
        self.identifier = identifier
        self.callback = callback
        self.strategy = strategy

    async def __call__(self, ws: WebSocket, context_key: str = ""):
        assert ACTRatelimit.backend is not None, "You must call FastAPILimiter.init in startup event of fastapi!"
        if self.milliseconds == 0:
            return
        identifier = self.identifier or ACTRatelimit.identifier
        strategy = self.strategy or ACTRatelimit.strategy
        rate_key = await identifier(ws)
        key = f"{ACTRatelimit.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await ACTRatelimit.backend.check(key, self.times, self.milliseconds, strategy)
        if pexpire != 0:
            callback = self.callback or ACTRatelimit.ws_callback
            return await callback(ws, pexpire)
