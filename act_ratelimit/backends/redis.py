from redis import asyncio as aioredis

from . import BaseBackend


class RedisBackend(BaseBackend):
    LUA_SCRIPT: str = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local expire_time = ARGV[2]

    local current = tonumber(redis.call('get', key) or "0")
    if current > 0 then
        if current + 1 > limit then
            return redis.call("PTTL",key)
        else
            redis.call("INCR", key)
            return 0
        end
    else
        redis.call("SET", key, 1,"px",expire_time)
        return 0
    end
    """

    def __init__(
        self,
        redis: aioredis.Redis[bytes],
        prefix: str = "fastapi-limiter",
    ):
        self.redis: aioredis.Redis[bytes] = redis
        self.prefix: str = prefix
        self.lua_sha: str | None = None

    async def check(self, key: str, times: int, limit: int) -> int:
        if not self.lua_sha:
            self.lua_sha = await self.redis.script_load(self.LUA_SCRIPT)  # pyright: ignore
        assert isinstance(self.lua_sha, str)  # pyright: ignore
        result: str = await self.redis.evalsha(self.lua_sha, 1, key, str(times), str(limit))  # pyright: ignore
        return int(result)  # pyright: ignore

    async def close(self) -> None:
        await self.redis.aclose()  # pyright: ignore
