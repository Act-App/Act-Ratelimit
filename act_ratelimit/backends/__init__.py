import abc


class BaseBackend(abc.ABC):
    @abc.abstractmethod
    async def check(self, key: str, times: int, limit: int) -> int:
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
        raise NotImplementedError
