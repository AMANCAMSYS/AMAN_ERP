"""
Shared rate limiter instance — استخدام مركزي لـ slowapi
SEC-001: Uses Redis backend for distributed rate limiting (falls back to in-memory)
"""
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def _build_storage_uri() -> str | None:
    """Return Redis URI if available, else None (in-memory fallback)."""
    try:
        from config import settings
        redis_url = settings.REDIS_URL
        if redis_url:
            # Quick connectivity check
            import redis as _redis
            r = _redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            logger.info("✅ Rate-limiter using Redis backend")
            return redis_url
    except Exception as exc:
        logger.warning(f"⚠️  Redis unavailable ({exc}); rate-limiter falling back to in-memory")
    return None


_storage_uri = _build_storage_uri()

# Global limiter — key by IP address, backed by Redis when available
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    storage_uri=_storage_uri,
)
