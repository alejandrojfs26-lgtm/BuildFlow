
import redis as _redis

from app.core.config import settings

_redis_pool: _redis.ConnectionPool | None = None


def _get_pool() -> _redis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = _redis.ConnectionPool.from_url(
            settings.redis_url, decode_responses=True
        )
    return _redis_pool


def get_client() -> _redis.Redis:
    return _redis.Redis(connection_pool=_get_pool())


def cache_get(key: str) -> str | None:
    r = get_client()
    return r.get(key)


def cache_set(key: str, value: str, ttl: int = 300) -> None:
    r = get_client()
    r.setex(key, ttl, value)


def cache_delete(key: str) -> None:
    r = get_client()
    r.delete(key)


def cache_delete_pattern(pattern: str) -> None:
    r = get_client()
    for key in r.scan_iter(match=pattern):
        r.delete(key)
