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
from __future__ import annotations

import abc

import typing_extensions

from act_ratelimit.constants import RateLimitStrategy

if typing_extensions.TYPE_CHECKING:
    from redis import asyncio as aioredis
    from valkey.asyncio import Valkey


__all__: tuple[str, ...] = ("BaseBackend", "RedisBackend", "ValkeyBackend")


class BaseBackend(abc.ABC):
    @abc.abstractmethod
    async def check(self, key: str, times: int, limit: int, strategy: RateLimitStrategy) -> int:
        """Check if a key has hit the rate limit.

        This method should return the time in milliseconds until the rate limit resets.
        If the rate limit has not been hit, it should return 0.

        Args:
            key: The key to check.
            times: The number of times the key has to be hit to trigger the rate limit.
            limit: How lo
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the connection to the backend."""
        raise NotImplementedError


class ValkeyBackend(BaseBackend):
    LUA_SCRIPT: str = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = ARGV[2]

        local current = tonumber(server.call('get', key) or "0")
        if current > 0 then
            if current + 1 > limit then
                return server.call("PTTL",key)
            else
                server.call("INCR", key)
                return 0
            end
        else
            server.call("SET", key, 1,"px",expire_time)
            return 0
        end
    """

    LUA_SCRIPT_SLIDING_WINDOW: str = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = tonumber(ARGV[2])
        local current_time = redis.call('TIME')[1]
        local start_time = current_time - expire_time / 1000
        redis.call('ZREMRANGEBYSCORE', key, 0, start_time)
        local current = redis.call('ZCARD', key)

        if current >= limit then
           return redis.call("PTTL",key)
        else
           redis.call("ZADD", key, current_time, current_time)
           redis.call('PEXPIRE', key, expire_time)
           return 0
        end
    """

    LUA_SCRIPT_FIXED_WINDOW_ELASTIIC: str = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = tonumber(ARGV[2])

        local current = tonumber(server.call('GET', key) or "0")

        if current > 0 then
            if current + 1 > limit then
                local ttl = server.call("PTTL", key)
                if ttl > 0 then
                    server.call("PEXPIRE", key, ttl + expire_time)  -- Extend timeout
                    return ttl + expire_time
                else
                    server.call("SET", key, 1, "px", expire_time)
                    return 0
                end
            else
                server.call("INCR", key)
                return 0
            end
        else
            server.call("SET", key, 1, "px", expire_time)
            return 0
        end
    """

    def __init__(
        self,
        valkey: Valkey,
    ):
        self.valkey: Valkey = valkey
        self.lua_sha_fixed: str | None = None
        self.lua_sha_sliding: str | None = None
        self.lua_sha_fixed_elastic: str | None = None

    async def check(self, key: str, times: int, limit: int, strategy: RateLimitStrategy) -> int:
        if strategy == RateLimitStrategy.FIXED_WINDOW:
            if not self.lua_sha_fixed:
                self.lua_sha_fixed = await self.valkey.script_load(self.LUA_SCRIPT)
            result: str = await self.valkey.evalsha(self.lua_sha_fixed, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore
        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            if not self.lua_sha_sliding:
                self.lua_sha_sliding = await self.valkey.script_load(self.LUA_SCRIPT_SLIDING_WINDOW)
            result: str = await self.valkey.evalsha(self.lua_sha_sliding, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore
        elif strategy == RateLimitStrategy.FIXED_WINDOW_ELASTIC:
            if not self.lua_sha_fixed_elastic:
                self.lua_sha_fixed_elastic = await self.valkey.script_load(self.LUA_SCRIPT_FIXED_WINDOW_ELASTIIC)
            result: str = await self.valkey.evalsha(self.lua_sha_fixed_elastic, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore

    async def close(self) -> None:
        await self.valkey.aclose()


class RedisBackend(BaseBackend):
    LUA_SCRIPT_FIXED_WINDOW: str = """
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

    LUA_SCRIPT_SLIDING_WINDOW: str = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = tonumber(ARGV[2])
        local current_time = redis.call('TIME')[1]
        local start_time = current_time - expire_time / 1000
        redis.call('ZREMRANGEBYSCORE', key, 0, start_time)
        local current = redis.call('ZCARD', key)

        if current >= limit then
            return redis.call("PTTL",key)
        else
            redis.call("ZADD", key, current_time, current_time)
            redis.call('PEXPIRE', key, expire_time)
            return 0
        end
    """

    LUA_SCRIPT_FIXED_WINDOW_ELASTIIC: str = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local expire_time = tonumber(ARGV[2])

    local current = tonumber(redis.call('GET', key) or "0")

    if current > 0 then
        if current + 1 > limit then
            local ttl = redis.call("PTTL", key)
            if ttl > 0 then
                redis.call("PEXPIRE", key, ttl + expire_time)  -- Extend timeout
                return ttl + expire_time
            else
                redis.call("SET", key, 1, "px", expire_time)
                return 0
            end
        else
            redis.call("INCR", key)
            return 0
        end
    else
        redis.call("SET", key, 1, "px", expire_time)
        return 0
    end
    """

    def __init__(
        self,
        redis: aioredis.Redis[bytes],
    ):
        self.redis: aioredis.Redis[bytes] = redis
        self.lua_sha_fixed: str | None = None
        self.lua_sha_sliding: str | None = None
        self.lua_sha_fixed_elastic: str | None = None

    async def check(self, key: str, times: int, limit: int, strategy: RateLimitStrategy) -> int:
        if strategy == RateLimitStrategy.FIXED_WINDOW:
            if not self.lua_sha_fixed:
                self.lua_sha_fixed = await self.redis.script_load(self.LUA_SCRIPT_FIXED_WINDOW)  # pyright: ignore
            result: str = await self.redis.evalsha(self.lua_sha_fixed, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore
        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            if not self.lua_sha_sliding:
                self.lua_sha_sliding = await self.redis.script_load(self.LUA_SCRIPT_SLIDING_WINDOW)  # pyright: ignore
            result: str = await self.redis.evalsha(self.lua_sha_sliding, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore
        elif strategy == RateLimitStrategy.FIXED_WINDOW_ELASTIC:
            if not self.lua_sha_fixed_elastic:
                self.lua_sha_fixed_elastic = await self.redis.script_load(self.LUA_SCRIPT_FIXED_WINDOW_ELASTIIC)  # pyright: ignore
            result: str = await self.redis.evalsha(self.lua_sha_fixed_elastic, 1, key, str(times), str(limit))  # pyright: ignore
            return int(result)  # pyright: ignore

    async def close(self) -> None:
        await self.redis.aclose()  # pyright: ignore
