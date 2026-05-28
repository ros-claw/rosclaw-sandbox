"""MuJoCo model cache — avoids reloading identical MJCF models."""

from __future__ import annotations

from typing import Any


class MujocoModelCache:
    """LRU cache for compiled MuJoCo MjModel instances."""

    _cache: dict[str, Any] = {}
    _max_size: int = 8

    @classmethod
    def get(cls, key: str) -> Any | None:
        return cls._cache.get(key)

    @classmethod
    def put(cls, key: str, model: Any) -> None:
        if len(cls._cache) >= cls._max_size:
            # Evict oldest
            oldest = next(iter(cls._cache))
            del cls._cache[oldest]
        cls._cache[key] = model

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def size(cls) -> int:
        return len(cls._cache)

    @classmethod
    def keys(cls) -> list[str]:
        return list(cls._cache.keys())
