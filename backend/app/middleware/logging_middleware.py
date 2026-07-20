"""Request logging middleware."""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing and correlation IDs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            logger.info(
                "Request started",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )

            try:
                response = await call_next(request)
                duration_ms = (time.time() - start) * 1000
                logger.info(
                    "Request complete",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )
                response.headers["X-Request-ID"] = request_id
                return response
            except Exception as e:
                logger.error("Request failed", error=str(e))
                raise
