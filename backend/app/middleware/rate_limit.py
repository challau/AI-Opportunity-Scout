"""Rate limiting middleware using Redis."""

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger()

RATE_LIMIT = 100  # requests per window
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter with Redis backing and in-memory fallback."""

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict = {}
        # Try to initialize redis client
        self.redis_client = None
        try:
            import redis.asyncio as aioredis
            from app.core.config import settings
            self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning("Failed to initialize Redis rate limiter, falling back to in-memory", error=str(e))

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Use Redis if available
        if self.redis_client:
            try:
                key = f"rate_limit:{client_ip}"
                # Use a transaction pipeline to increment and set expire
                async with self.redis_client.pipeline(transaction=True) as pipe:
                    pipe.multi()
                    pipe.incr(key)
                    pipe.expire(key, WINDOW_SECONDS)
                    res = await pipe.execute()

                request_count = res[0]
                if request_count > RATE_LIMIT:
                    logger.warning("Rate limit exceeded (Redis)", ip=client_ip, count=request_count)
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests. Please slow down."},
                    )
                return await call_next(request)
            except Exception as e:
                logger.warning("Redis rate limiting failed, falling back to in-memory", error=str(e))

        # Fallback: In-memory rate limiting
        window_start = now - WINDOW_SECONDS
        self._requests = {
            k: v for k, v in self._requests.items() if v and v[-1] > window_start
        }

        if client_ip not in self._requests:
            self._requests[client_ip] = []

        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]
        self._requests[client_ip].append(now)

        if len(self._requests[client_ip]) > RATE_LIMIT:
            logger.warning("Rate limit exceeded (In-memory)", ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )

        return await call_next(request)
