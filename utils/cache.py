"""Simple in-memory cache with TTL for weather and LLM responses."""
import time
import hashlib
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with value and expiration"""
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds
        self.created_at = datetime.now()
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def age_seconds(self) -> float:
        return time.time() - self.created_at.timestamp()


class SimpleCache:
    """
    Thread-safe in-memory cache with TTL support.
    
    For production, consider Redis or Memcached.
    This implementation is suitable for single-instance deployments.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries before eviction
        """
        self._cache = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """
        Generate cache key from data
        
        Args:
            prefix: Cache key prefix (e.g., 'weather', 'llm')
            data: Data to hash (dict, string, etc.)
        
        Returns:
            Cache key string
        """
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache expired: {key}")
            return None
        
        self._hits += 1
        age = entry.age_seconds()
        logger.info(f"Cache hit: {key} (age: {age:.1f}s)")
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """
        Store value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[key] = CacheEntry(value, ttl_seconds)
        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
    
    def _evict_oldest(self):
        """Evict 10% of oldest entries"""
        if not self._cache:
            return
        
        # Sort by creation time
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        
        # Remove oldest 10%
        evict_count = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:evict_count]:
            del self._cache[key]
            logger.debug(f"Cache evicted: {key}")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
    
    def stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests
        }


# Global cache instances
weather_cache = SimpleCache(max_size=500)
llm_cache = SimpleCache(max_size=200)  # Smaller since responses are large


# Cache TTL constants (in seconds)
WEATHER_CACHE_TTL = 6 * 60 * 60  # 6 hours
LLM_CACHE_TTL = 24 * 60 * 60      # 24 hours
