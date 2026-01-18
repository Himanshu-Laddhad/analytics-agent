import redis
import json
import hashlib
from typing import Optional, Any
import logging
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
    def _generate_key(self, query: str, schema_version: str = "v1") -> str:
        """Generate deterministic cache key"""
        content = f"{query}:{schema_version}"
        return f"analytics:{hashlib.sha256(content.encode()).hexdigest()}"
    
    def get(self, query: str) -> Optional[dict]:
        """Retrieve cached result"""
        try:
            key = self._generate_key(query)
            data = self.client.get(key)
            if data:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return json.loads(data)
            logger.info(f"Cache MISS for query: {query[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, query: str, value: dict, ttl: int = None) -> bool:
        """Store result in cache"""
        try:
            key = self._generate_key(query)
            ttl = ttl or settings.REDIS_TTL
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)  # Handle datetime/decimal
            )
            logger.info(f"Cached result for: {query[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            self.client.ping()
            return True
        except:
            return False

# Singleton instance
cache = RedisCache()