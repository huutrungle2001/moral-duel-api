from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from app.config import settings


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Remove old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            
            # Check if under limit
            if len(self.requests[key]) >= max_requests:
                return False
            
            # Add current request
            self.requests[key].append(now)
            return True


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and in development mode
        if request.url.path in ["/", "/health"] or settings.DEBUG:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Determine rate limit based on endpoint
        rate_limit = None
        window = 60  # 1 minute window
        
        if request.url.path.startswith("/auth"):
            rate_limit = 5  # 5 requests per minute
        elif request.url.path.startswith("/cases") and request.method == "POST":
            rate_limit = 3  # 3 case creations per hour
            window = 3600
        elif "/vote" in request.url.path:
            rate_limit = 10  # 10 votes per minute
        
        # Apply rate limit if configured
        if rate_limit:
            key = f"{client_ip}:{request.url.path}"
            allowed = await rate_limiter.is_allowed(key, rate_limit, window)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
        
        response = await call_next(request)
        return response
