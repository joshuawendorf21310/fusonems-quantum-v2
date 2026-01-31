"""
Redis-based distributed rate limiting
Replaces in-memory rate limiting with Redis for multi-instance deployments
"""
from datetime import datetime, timedelta
from typing import Optional
import redis
import logging
from fastapi import HTTPException, Request, status
from core.config import settings

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis
    Works across multiple application instances
    """
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.warning(f"Redis rate limiter disabled - {e}")
            self.enabled = False
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if rate limit is exceeded
        
        Args:
            key: Unique identifier for the rate limit (e.g., IP address, user ID)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        if not self.enabled:
            return True, None
        
        try:
            # Use Redis sorted set to track requests in a sliding window
            now = datetime.now().timestamp()
            window_start = now - window_seconds
            
            # Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old requests outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry on the key
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            request_count = results[1]
            
            if request_count >= max_requests:
                # Rate limit exceeded
                # Calculate retry after time
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    oldest_timestamp = oldest_request[0][1]
                    retry_after = int(window_seconds - (now - oldest_timestamp))
                    return False, max(retry_after, 1)
                return False, window_seconds
            
            return True, None
            
        except redis.RedisError as e:
            # If Redis fails, allow the request (fail open)
            logger.error(f"Redis rate limit error: {e}")
            return True, None


# Global rate limiter instance
rate_limiter = RedisRateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Use IP address as rate limit key
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}:{request.url.path}"
            
            is_allowed, retry_after = rate_limiter.check_rate_limit(
                key, max_requests, window_seconds
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)} if retry_after else {}
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
