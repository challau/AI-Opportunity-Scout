"""
AI Opportunity Scout — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, events, users, resume, search, notifications, ai, admin
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.session import engine
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.scheduler.scheduler import start_scheduler, shutdown_scheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    logger.info("Starting AI Opportunity Scout API", version=settings.APP_VERSION)

    # Validate that production secrets have been properly configured
    settings.validate_production_settings()

    # Verify Redis connection
    import redis.asyncio as aioredis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        logger.info("Connected to Redis successfully")
        await r.close()
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))

    # Start background scheduler
    start_scheduler()
    logger.info("Scheduler started")

    yield

    # Cleanup
    shutdown_scheduler()
    await engine.dispose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    import os
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # API docs: disable in production unless DOCS_ENABLED=true is set
    import os
    docs_enabled = not settings.is_production or os.getenv("DOCS_ENABLED", "").lower() == "true"
    docs_url = "/docs" if docs_enabled else None
    redoc_url = "/redoc" if docs_enabled else None
    openapi_url = "/openapi.json" if docs_enabled else None

    app = FastAPI(
        title="AI Opportunity Scout API",
        description="""
        ## AI Opportunity Scout

        Automatically discover hackathons, coding contests, internships, and developer events.
        Powered by AI agents for ranking, deduplication, and personalized recommendations.

        ### Features
        - 🔍 Keyword & Semantic Search
        - 🤖 AI-powered recommendations
        - 📧 Email & Telegram notifications
        - 📄 Resume matching
        - 🕷️ 15+ platform crawlers
        """,
        version=settings.APP_VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # ─── Middleware ───────────────────────────────────────────────────────────
    # Build CORS origins: configured list + Railway/Vercel wildcard origins
    cors_origins = list(settings.CORS_ORIGINS)
    # In production, also allow any *.vercel.app and *.railway.app by regex
    cors_origin_regex = r"https://(.*\.vercel\.app|.*\.railway\.app|localhost:\d+)" if settings.is_production else None
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=cors_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # ─── Static Files ─────────────────────────────────────────────────────────
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # ─── Routers ──────────────────────────────────────────────────────────────
    prefix = settings.API_V1_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(events.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(resume.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)
    app.include_router(notifications.router, prefix=prefix)
    app.include_router(ai.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    
    from app.api import scheduler as scheduler_api
    app.include_router(scheduler_api.router, prefix=prefix)

    # ─── Health Check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        from app.scheduler.scheduler import get_scheduler_status_details
        scheduler_status = await get_scheduler_status_details()
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "scheduler": scheduler_status
        }

    return app


app = create_app()
