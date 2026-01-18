import redis
import json
from typing import Optional, Any
from app.config import settings


# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Redis client'ı al veya oluştur (singleton pattern)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return _redis_client


def rate_limit_check(key: str, limit: int, window: int) -> tuple[bool, int]:
    """
    Rate limiting kontrolü yap
    Returns: (is_allowed, remaining_attempts)
    """
    try:
        client = get_redis_client()
        current = client.incr(key)
        
        # İlk istekte TTL ayarla
        if current == 1:
            client.expire(key, window)
        
        remaining = max(0, limit - current)
        is_allowed = current <= limit
        
        return is_allowed, remaining
    except Exception as e:
        print(f"Redis rate_limit_check error: {e}")
        # Redis hatası durumunda izin ver (fail-open)
        return True, limit


def rate_limit_reset(key: str) -> bool:
    """Rate limit key'ini sıfırla"""
    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except Exception as e:
        print(f"Redis rate_limit_reset error: {e}")
        return False


def cache_get(key: str) -> Optional[Any]:
    """Redis'ten veri getir"""
    try:
        client = get_redis_client()
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Redis cache_get error: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 600) -> bool:
    """Redis'e veri kaydet (TTL ile)"""
    try:
        client = get_redis_client()
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        print(f"Redis cache_set error: {e}")
        return False
