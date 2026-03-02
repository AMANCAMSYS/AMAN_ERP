
import json
import logging
from typing import Any, Optional, Union, Callable
import pickle
import hashlib
from datetime import timedelta
from functools import wraps
from config import settings

logger = logging.getLogger(__name__)

class MemoryCache:
    def __init__(self):
        self._cache = {}
        self._expiry = {}
        import time
        self._time = time
        
    def get(self, key: str) -> Optional[Any]:
        if key in self._expiry:
            if self._time.time() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
        return self._cache.get(key)
        
    def set(self, key: str, value: Any, expire: int = 300):
        self._cache[key] = value
        self._expiry[key] = self._time.time() + expire
        
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
            
    def delete_pattern(self, pattern: str):
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self._cache[k]
            if k in self._expiry:
                del self._expiry[k]

    def flush(self):
        self._cache.clear()
        self._expiry.clear()


class RedisCache:
    def __init__(self, url: str):
        try:
            import redis
            self.redis = redis.from_url(url)
            self.enabled = True
        except (ImportError, Exception) as e:
            logger.warning(f"Redis not available, falling back to memory cache: {e}")
            self.enabled = False
            self.memory = MemoryCache()

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return self.memory.get(key)
        try:
            val = self.redis.get(key)
            if val:
                return pickle.loads(val)
            return None
        except Exception as e: # Redis failure
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 300):
        if not self.enabled:
            return self.memory.set(key, value, expire)
        try:
            self.redis.setex(key, timedelta(seconds=expire), pickle.dumps(value))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str):
        if not self.enabled:
            return self.memory.delete(key)
        try:
            self.redis.delete(key)
        except Exception:
            pass
            
    def delete_pattern(self, pattern: str):
        if not self.enabled:
            return self.memory.delete_pattern(pattern)
        try:
            # Not extremely efficient for production redis but okay here
            keys = self.redis.keys(f"*{pattern}*")
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass

# Initialize cache
if settings.REDIS_URL:
    cache = RedisCache(settings.REDIS_URL)
else:
    cache = MemoryCache()


def cached(prefix: str, expire: int = 300, company_specific: bool = True):
    """
    Decorator for caching FastAPI endpoint responses.
    
    Usage:
        @router.get("/heavy-query")
        @cached("dashboard_stats", expire=120)
        def get_stats(current_user = Depends(get_current_user)):
            ...
    
    Args:
        prefix: Cache key prefix (e.g., "dashboard", "reports")
        expire: Cache TTL in seconds (default: 5 minutes)
        company_specific: If True, includes company_id in cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name + arguments
            key_parts = [prefix, func.__name__]
            
            # Add company_id if available
            current_user = kwargs.get('current_user')
            if company_specific and current_user:
                if isinstance(current_user, dict):
                    cid = current_user.get('company_id', '')
                else:
                    cid = getattr(current_user, 'company_id', '')
                key_parts.append(str(cid))

            # Hash relevant kwargs (excluding current_user)
            relevant_kwargs = {
                k: str(v) for k, v in kwargs.items()
                if k not in ('current_user', 'db', 'request') and v is not None
            }
            if relevant_kwargs:
                args_hash = hashlib.md5(
                    json.dumps(relevant_kwargs, sort_keys=True, default=str).encode()
                ).hexdigest()[:12]
                key_parts.append(args_hash)

            cache_key = ":".join(key_parts)

            # Try cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            try:
                cache.set(cache_key, result, expire)
                logger.debug(f"Cache SET: {cache_key} (TTL={expire}s)")
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate all cache keys matching a pattern"""
    cache.delete_pattern(pattern)


def invalidate_company_cache(company_id: str, module: str = ""):
    """Invalidate all cache for a specific company and optional module"""
    pattern = f"{module}:{company_id}" if module else str(company_id)
    cache.delete_pattern(pattern)
