# Act-Ratelimit

[![pypi](https://img.shields.io/pypi/v/act-ratelimit.svg?style=flat)](https://pypi.python.org/pypi/fastapi-limiter)
[![license](https://img.shields.io/github/license/Act-App/Act-Ratelimit)](https://github.com/Act-App/Act-Ratelimit/blob/master/LICENCE)

## Introduction

Act-Ratelimit is a rate limiting tool for [fastapi](https://github.com/tiangolo/fastapi).<br>
It is a fork of [fastapi-limiter](https://github.com/long2ice/fastapi-limiter) with support for multiple Datastores and different Ratelimit strategies.

## Requirements

- [fastapi](https://github.com/tiangolo/fastapi)

## Additional Requirements
- [redis](https://github.com/redis/redis-py) if you want to use the redis-backend
- [valkey](https://github.com/valkey-io/valkey-py) if you want to use the valkey-backend

## Install

Just install from pypi

```shell script
pip install act-ratelimit
```

You can also install the additional requirements

```shell script
pip install act-ratelimit[redis]
pip install act-ratelimit[valkey]
```

## Quick Start

Act-Ratelimit is simple to use, you need to initialize it with your preferred backend and then use the `RateLimiter` dependency in your routes.

```py
import redis.asyncio as redis
from contextlib import asynccontextmanager

from act_ratelimit import ACTRatelimit
from act_ratelimit.depends import RateLimiter
from act_ratelimit.backends import RedisBackend


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_backend = RedisBackend(
        redis.from_url("redis://localhost:6379", encoding="utf8"), prefix="act-ratelimit-example"
    )
    await ACTRatelimit.init(redis_backend)
    yield
    await ACTRatelimit.close()


app = FastAPI(lifespan=lifespan)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def index():
    return {"msg": "Hello World"}
```

> [!NOTE]
> For people coming from fastapi-limiter, the `FastAPILimiter.init` method has changed. It now takes a backend instance instead of a redis instance.

## Usage

You will first need to initialize the `ACTRatelimit` with a [`backend`](#backend) instance.

Other possible parameters are:
- [`identifier`](#identifier) - The identifier of the rate limit, default is `ip`.
- [`callback`](#callback) - The callback when the rate limit is exceeded.
- [`strategy`](#strategies) - The strategy to use for the rate limit, default is `FIXED_WINDOW`.




### Backend

There are currently two backends pre-implemented, `RedisBackend` and `ValkeyBackend`.

`RedisBackend` uses the `redis` library to interact with a redis instance.<br>
`ValkeyBackend` uses the `valkey` library to interact with a valkey instance.

You can also implement your own backend by inheriting from the `BaseBackend` class.

```py
from act_ratelimit.backends import BaseBackend
from act_ratelimit.constants import RateLimitStrategy

class MyBackend(BaseBackend):
    
    async def check(self, key: str, times: int, limit: int, strategy: RateLimitStrategy) -> int:
        """Check if a key has hit the rate limit.
    
        This method should return the time in milliseconds until the rate limit resets.
        If the rate limit has not been hit, it should return 0.
    
        Args:
            key: The key to check.
            times: The number of times the key has to be hit to trigger the rate limit.
            limit: How long the rate limit should last in milliseconds.
        """
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection to the backend."""
        raise NotImplementedError
```
### Strategies

There are currently three strategies available, `FIXED_WINDOW`, `SLIDING_WINDOW` and `FIXED_WINDOW_ELASTIC`.

> [!NOTE]
> These Strategies need to be implemented in the backend. If you are using a custom backend, you will need to implement these strategies.

### Identifier

Identifier of route limit, default is `ip`, you can override it such as `userid` and so on.

```py
async def default_identifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host + ":" + request.scope["path"]
```

### Callback

Callback when access is forbidden, default is raise `HTTPException` with `429` status code.

```py
async def default_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """

    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", headers={"Retry-After": str(pexpire)}
    )
```

## Multiple limiters

You can use multiple limiters in one route.

```py
@app.get(
    "/multiple",
    dependencies=[
        Depends(RateLimiter(times=1, seconds=5)),
        Depends(RateLimiter(times=2, seconds=15)),
    ],
)
async def multiple():
    return {"msg": "Hello World"}
```

Not that you should note the dependencies orders, keep lower of result of `seconds/times` at the first.

## Rate limiting within a websocket.

While the above examples work with rest requests, FastAPI also allows easy usage
of websockets, which require a slightly different approach.

Because websockets are likely to be long lived, you may want to rate limit in
response to data sent over the socket.

You can do this by rate limiting within the body of the websocket handler:

```py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)  # NB: context_key is optional
            await websocket.send_text(f"Hello, world")
        except WebSocketRateLimitException:  # Thrown when rate limit exceeded.
            await websocket.send_text(f"Hello again")
```

## License

This project is licensed under the
[Apache-2.0](https://github.com/long2ice/fastapi-limiter/blob/master/LICENCE) License.
