
import json
import logging
from typing import Any, Optional, Union
import pickle
from datetime import timedelta
from config import settings

logger = logging.getLogger(__name__)

class MemoryCache:
    def __init__(self):
        self._cache = {}
        
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
        
    def set(self, key: str, value: Any, expire: int = 300):
        self._cache[key] = value
        
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            
    def delete_pattern(self, pattern: str):
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self._cache[k]


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
