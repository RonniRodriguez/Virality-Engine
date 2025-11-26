"""
Idea Inc - Cache Utilities

Redis-based caching with fallback to in-memory cache.
Supports world snapshots, leaderboards, and session data.
"""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value with optional TTL (seconds)"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key"""
        pass
    
    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        pass


class InMemoryCache(CacheBackend):
    """
    In-memory cache for development and testing.
    
    Provides basic caching without external dependencies.
    """
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            if key not in self._data:
                return None
            
            entry = self._data[key]
            
            # Check expiration
            if entry["expires_at"] and datetime.utcnow() > entry["expires_at"]:
                del self._data[key]
                return None
            
            return entry["value"]
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        async with self._lock:
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            self._data[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.utcnow(),
            }
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None
    
    async def expire(self, key: str, ttl: int) -> bool:
        async with self._lock:
            if key not in self._data:
                return False
            
            self._data[key]["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
            return True
    
    async def incr(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            if key not in self._data:
                self._data[key] = {
                    "value": "0",
                    "expires_at": None,
                    "created_at": datetime.utcnow(),
                }
            
            current = int(self._data[key]["value"])
            new_value = current + amount
            self._data[key]["value"] = str(new_value)
            return new_value
    
    async def keys(self, pattern: str) -> List[str]:
        """Simple pattern matching (supports * wildcard)"""
        import fnmatch
        
        async with self._lock:
            # Clean expired keys
            now = datetime.utcnow()
            expired = [
                k for k, v in self._data.items()
                if v["expires_at"] and now > v["expires_at"]
            ]
            for k in expired:
                del self._data[k]
            
            # Match pattern
            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
    
    async def clear(self) -> None:
        """Clear all data"""
        async with self._lock:
            self._data.clear()


class RedisCache(CacheBackend):
    """
    Redis-based cache for production.
    
    Requires redis package and running Redis server.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client = None
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            import redis.asyncio as redis
            
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            
            # Test connection
            await self._client.ping()
            logger.info("Redis cache connected", url=self.redis_url)
            
        except ImportError:
            logger.error("redis package not installed")
            raise
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            logger.info("Redis cache disconnected")
    
    async def get(self, key: str) -> Optional[str]:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return await self._client.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        if not self._client:
            raise RuntimeError("Redis not connected")
        
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)
        return True
    
    async def delete(self, key: str) -> bool:
        if not self._client:
            raise RuntimeError("Redis not connected")
        result = await self._client.delete(key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return await self._client.exists(key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return await self._client.expire(key, ttl)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return await self._client.incrby(key, amount)
    
    async def keys(self, pattern: str) -> List[str]:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return await self._client.keys(pattern)


class Cache:
    """
    High-level cache interface with JSON serialization.
    
    Wraps a cache backend and provides convenient methods
    for common caching operations.
    """
    
    def __init__(self, backend: CacheBackend, prefix: str = "ideainc"):
        self.backend = backend
        self.prefix = prefix
    
    def _key(self, key: str) -> str:
        """Generate prefixed key"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get and deserialize a value"""
        value = await self.backend.get(self._key(key))
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Serialize and set a value"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        elif not isinstance(value, str):
            value = str(value)
        
        return await self.backend.set(self._key(key), value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        return await self.backend.delete(self._key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.backend.exists(self._key(key))
    
    # ==========================================================================
    # World Snapshot Caching
    # ==========================================================================
    
    async def cache_snapshot(
        self,
        world_id: str,
        snapshot: Dict[str, Any],
        ttl: int = 60,
    ) -> bool:
        """Cache a world snapshot"""
        key = f"snapshot:{world_id}"
        return await self.set(key, snapshot, ttl)
    
    async def get_snapshot(self, world_id: str) -> Optional[Dict[str, Any]]:
        """Get cached world snapshot"""
        key = f"snapshot:{world_id}"
        return await self.get(key)
    
    async def invalidate_snapshot(self, world_id: str) -> bool:
        """Invalidate cached snapshot"""
        key = f"snapshot:{world_id}"
        return await self.delete(key)
    
    # ==========================================================================
    # Leaderboard Caching
    # ==========================================================================
    
    async def cache_leaderboard(
        self,
        world_id: str,
        leaderboard: List[Dict[str, Any]],
        ttl: int = 30,
    ) -> bool:
        """Cache a leaderboard"""
        key = f"leaderboard:{world_id}"
        return await self.set(key, leaderboard, ttl)
    
    async def get_leaderboard(self, world_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached leaderboard"""
        key = f"leaderboard:{world_id}"
        return await self.get(key)
    
    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int,
    ) -> tuple[bool, int]:
        """
        Check rate limit for an identifier.
        
        Args:
            identifier: User ID, IP, etc.
            limit: Maximum requests in window
            window: Time window in seconds
        
        Returns:
            Tuple of (allowed, remaining)
        """
        key = f"ratelimit:{identifier}"
        
        # Check if key exists
        if not await self.backend.exists(self._key(key)):
            # First request in window
            await self.backend.set(self._key(key), "1", window)
            return True, limit - 1
        
        # Increment counter
        count = await self.backend.incr(self._key(key))
        
        if count > limit:
            return False, 0
        
        return True, limit - count
    
    # ==========================================================================
    # Session Caching
    # ==========================================================================
    
    async def cache_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 3600,
    ) -> bool:
        """Cache session data"""
        key = f"session:{session_id}"
        return await self.set(key, data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = f"session:{session_id}"
        return await self.delete(key)


def create_cache(
    use_redis: bool = False,
    redis_url: str = "redis://localhost:6379/0",
    prefix: str = "ideainc",
) -> Cache:
    """
    Factory function to create cache instance.
    
    Args:
        use_redis: Whether to use Redis
        redis_url: Redis connection URL
        prefix: Key prefix
    
    Returns:
        Cache instance
    """
    if use_redis:
        backend = RedisCache(redis_url)
    else:
        backend = InMemoryCache()
    
    return Cache(backend, prefix)

