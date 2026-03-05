from __future__ import annotations

import json
import os
import time
from importlib import import_module
from typing import Any, Protocol


class CacheBackend(Protocol):
    def get_json(self, key: str) -> dict[str, Any] | None:
        ...

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        ...

    def invalidate_namespace(self, namespace: str) -> int:
        ...


class InMemoryJsonCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float | None, str]] = {}

    def get_json(self, key: str) -> dict[str, Any] | None:
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, payload = item
        if expires_at is not None and expires_at < time.time():
            self._store.pop(key, None)
            return None
        return json.loads(payload)

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        expires_at = None if ttl_seconds <= 0 else time.time() + ttl_seconds
        self._store[key] = (expires_at, json.dumps(value, sort_keys=True))

    def invalidate_namespace(self, namespace: str) -> int:
        prefix = "f1:" if namespace == "all" else f"f1:{namespace}:"
        keys = [key for key in self._store if key.startswith(prefix)]
        for key in keys:
            self._store.pop(key, None)
        return len(keys)


class RedisJsonCache:
    def __init__(self, redis_url: str) -> None:
        redis_module = import_module("redis")
        self._client = redis_module.Redis.from_url(redis_url, decode_responses=True)

    def get_json(self, key: str) -> dict[str, Any] | None:
        payload = self._client.get(key)
        if payload is None:
            return None
        return json.loads(payload)

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        payload = json.dumps(value, sort_keys=True)
        if ttl_seconds > 0:
            self._client.setex(key, ttl_seconds, payload)
            return
        self._client.set(key, payload)

    def invalidate_namespace(self, namespace: str) -> int:
        pattern = "f1:*" if namespace == "all" else f"f1:{namespace}:*"
        keys = list(self._client.scan_iter(match=pattern, count=1000))
        if not keys:
            return 0
        return int(self._client.delete(*keys))


def build_cache_backend() -> CacheBackend:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return InMemoryJsonCache()

    try:
        backend = RedisJsonCache(redis_url)
        backend.set_json("f1:cache:health", {"ok": True}, ttl_seconds=5)
        return backend
    except Exception:
        # Keep local development stable when Redis is unreachable.
        return InMemoryJsonCache()


CACHE = build_cache_backend()


def make_cache_key(
    namespace: str,
    *,
    ruleset_hash: str,
    model_version: str,
    data_cut: str,
    request_params: dict[str, Any],
) -> str:
    normalized = json.dumps(request_params, sort_keys=True, separators=(",", ":"))
    return (
        f"f1:{namespace}:rules={ruleset_hash}:model={model_version}:"
        f"data_cut={data_cut}:request={normalized}"
    )
