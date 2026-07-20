"""Application configuration using Pydantic Settings."""

import os
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_async_db_url(url: str) -> str:
    """Coerce any postgres URL into the asyncpg driver form SQLAlchemy needs.

    Railway/Heroku-style URLs come as postgres:// or postgresql:// which load
    psycopg2 (sync) and crash create_async_engine. asyncpg also rejects
    libpq-style ?sslmode= — translate it to ?ssl=.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    url = url.replace("sslmode=", "ssl=")
    # asyncpg only understands a subset of ssl values; map verify modes to require
    url = url.replace("ssl=verify-full", "ssl=require").replace("ssl=verify-ca", "ssl=require")
    # channel_binding is a libpq-only param asyncpg rejects
    if "channel_binding=" in url:
        import re
        url = re.sub(r"[?&]channel_binding=[^&]*", "", url)
    return url


def _normalize_sync_db_url(url: str) -> str:
    """Coerce any postgres URL into the plain psycopg2 form Alembic uses."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    # psycopg2 uses sslmode=, not ssl=
    url = url.replace("?ssl=require", "?sslmode=require").replace("&ssl=require", "&sslmode=require")
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Opportunity Scout"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Database ─────────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_opportunity_scout"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_opportunity_scout"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/ai_opportunity_scout"

    # ─── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── OpenAI ───────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ─── Google OAuth ─────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # ─── GitHub OAuth ─────────────────────────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"

    # ─── Email ────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@aiopportunityscout.com"
    SMTP_FROM_NAME: str = "AI Opportunity Scout"
    SENDGRID_API_KEY: str = ""
    # Alias some deployments use instead of SMTP_FROM_EMAIL
    SMTP_FROM: str = ""
    # Default recipient for test/system notifications
    NOTIFICATION_EMAIL: str = ""
    # Brevo HTTPS API key (xkeysib-...) — preferred over SMTP on hosts that
    # block outbound SMTP ports (e.g. Railway)
    BREVO_API_KEY: str = ""

    # ─── Telegram ─────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # ─── Scheduler ────────────────────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_INTERVAL_HOURS: int = 6
    SCHEDULER_DAILY_DIGEST_HOUR: int = 8
    SCHEDULER_DAILY_DIGEST_MINUTE: int = 0
    SCHEDULER_REMINDER_HOUR: int = 7
    SCHEDULER_REMINDER_MINUTE: int = 0
    SCHEDULER_MAX_CRAWL_RETRIES: int = 3
    SCHEDULER_CRAWL_RETRY_DELAY_SECONDS: int = 300
    SCHEDULER_LOCK_TTL_SECONDS: int = 3600

    # ─── Crawling ─────────────────────────────────────────────────────────────
    PLAYWRIGHT_HEADLESS: bool = True
    CRAWL_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RATE_LIMIT_DELAY: float = 2.0

    # ─── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    # ─── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Tolerate plain comma-separated values
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def normalize_database_urls(self):
        # SMTP_FROM is an accepted alias for SMTP_FROM_EMAIL
        if self.SMTP_FROM and not os.getenv("SMTP_FROM_EMAIL"):
            self.SMTP_FROM_EMAIL = self.SMTP_FROM
        # Detect Railway: treat its environment as production unless APP_ENV
        # was set explicitly.
        if os.getenv("RAILWAY_ENVIRONMENT") and not os.getenv("APP_ENV"):
            self.APP_ENV = os.getenv("RAILWAY_ENVIRONMENT_NAME", "production") or "production"
        # Railway injects DATABASE_URL as postgres://...; derive both driver
        # variants from whatever we were given so migrations and runtime work.
        raw = self.DATABASE_URL or self.DATABASE_URL_SYNC
        sync_raw = os.getenv("DATABASE_URL_SYNC") or raw
        self.DATABASE_URL = _normalize_async_db_url(raw)
        self.DATABASE_URL_SYNC = _normalize_sync_db_url(sync_raw)
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def scheduler_should_run(self) -> bool:
        return self.SCHEDULER_ENABLED or self.is_production

    def validate_production_settings(self) -> None:
        """Raise if dangerous defaults remain in a production environment."""
        if self.is_production:
            dangerous_defaults = [
                "change-me-in-production",
                "your-super-secret",
                "secret",
            ]
            for placeholder in dangerous_defaults:
                if placeholder in self.SECRET_KEY.lower():
                    raise RuntimeError(
                        "SECRET_KEY must be changed from the default before running in production! "
                        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                    )


settings = Settings()
