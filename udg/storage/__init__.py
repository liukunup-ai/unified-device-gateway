from abc import ABC, abstractmethod
from typing import Optional


class Storage(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        ...


class MemoryStorage(Storage):
    def __init__(self):
        self._data: dict[str, dict] = {}

    async def get(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def list_keys(self, prefix: str = "") -> list[str]:
        return [k for k in self._data.keys() if k.startswith(prefix)]


class RedisStorage(Storage):
    def __init__(self, redis_url: str):
        self._redis_url = redis_url

    async def get(self, key: str) -> Optional[dict]:
        raise NotImplementedError("RedisStorage not yet implemented")

    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        raise NotImplementedError("RedisStorage not yet implemented")

    async def delete(self, key: str) -> None:
        raise NotImplementedError("RedisStorage not yet implemented")

    async def list_keys(self, prefix: str = "") -> list[str]:
        raise NotImplementedError("RedisStorage not yet implemented")


def create_storage(redis_url: Optional[str] = None) -> Storage:
    if redis_url:
        return RedisStorage(redis_url)
    return MemoryStorage()