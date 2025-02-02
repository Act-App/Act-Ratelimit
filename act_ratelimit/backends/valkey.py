from __future__ import annotations

import typing_extensions

if typing_extensions.TYPE_CHECKING:
    from valkey.asyncio import Valkey

from . import BaseBackend


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

    def __init__(
        self,
        valkey: Valkey,
        prefix: str = "fastapi-limiter",
    ):
        self.valkey: Valkey = valkey
        self.prefix: str = prefix
        self.lua_sha: str | None = None

    async def check(self, key: str, times: int, limit: int) -> int:
        if not self.lua_sha:
            self.lua_sha = await self.valkey.script_load(self.LUA_SCRIPT)
        assert isinstance(self.lua_sha, str)
        result: str = await self.valkey.evalsha(self.lua_sha, 1, key, str(times), str(limit))  # pyright: ignore
        return int(result)  # pyright: ignore

    async def close(self) -> None:
        await self.valkey.aclose()
