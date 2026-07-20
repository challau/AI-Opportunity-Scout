"""APScheduler configuration and lifecycle management with Redis-based locking."""

import asyncio
from typing import Optional
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
import redis.asyncio as aioredis
from pytz import timezone

from app.core.config import settings
from app.scheduler.lock import acquire_lock, release_lock, refresh_lock, get_lock_info
from app.scheduler.tasks import run_crawl_task, run_daily_digest, run_deadline_reminders

logger = structlog.get_logger()

_scheduler: Optional[AsyncIOScheduler] = None
_lock_refresh_task: Optional[asyncio.Task] = None
_redis_client: Optional[aioredis.Redis] = None


async def _refresh_lock_loop():
    """Background task to periodically refresh the Redis scheduler lock."""
    global _redis_client
    # Refresh every (LOCK_TTL / 2) seconds
    interval = max(10, int(settings.SCHEDULER_LOCK_TTL_SECONDS / 2))
    
    while True:
        try:
            await asyncio.sleep(interval)
            if _redis_client:
                refreshed = await refresh_lock(_redis_client, settings.SCHEDULER_LOCK_TTL_SECONDS)
                if not refreshed:
                    logger.critical("Failed to refresh scheduler lock! Shutting down scheduler to prevent split-brain.")
                    await shutdown_scheduler()
                    break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in scheduler lock refresh loop", error=str(e))
            await asyncio.sleep(5)  # Quick retry on error


async def start_scheduler_async() -> None:
    """Async startup helper for scheduler."""
    global _scheduler, _lock_refresh_task, _redis_client

    if not settings.scheduler_should_run:
        logger.info("Scheduler is disabled in this environment settings.")
        return

    logger.info("Attempting to start scheduler...")

    # Initialize redis client
    _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Attempt to acquire lock
    lock_acquired = await acquire_lock(_redis_client, settings.SCHEDULER_LOCK_TTL_SECONDS)
    if not lock_acquired:
        owner, ttl = await get_lock_info(_redis_client)
        logger.warning(
            "Scheduler lock is held by another instance. Running in standby mode.",
            owner=owner,
            ttl=ttl
        )
        await _redis_client.close()
        _redis_client = None
        return

    # Start lock refresh loop
    _lock_refresh_task = asyncio.create_task(_refresh_lock_loop())

    _scheduler = AsyncIOScheduler(timezone=timezone(settings.SCHEDULER_TIMEZONE))

    # ─── Crawler jobs (Interval) ──────────────────────────────────────────────
    _scheduler.add_job(
        func=run_crawl_task,
        args=["all", "scheduled"],
        trigger=IntervalTrigger(hours=settings.SCHEDULER_INTERVAL_HOURS),
        id="crawl_all",
        name="Crawl all platforms",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # ─── Daily digest (Cron) ──────────────────────────────────────────────────
    _scheduler.add_job(
        func=run_daily_digest,
        args=["scheduled"],
        trigger=CronTrigger(
            hour=settings.SCHEDULER_DAILY_DIGEST_HOUR,
            minute=settings.SCHEDULER_DAILY_DIGEST_MINUTE,
        ),
        id="daily_digest",
        name="Send daily digest",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    # ─── Deadline reminders (Cron) ────────────────────────────────────────────
    _scheduler.add_job(
        func=run_deadline_reminders,
        args=["scheduled"],
        trigger=CronTrigger(
            hour=settings.SCHEDULER_REMINDER_HOUR,
            minute=settings.SCHEDULER_REMINDER_MINUTE,
        ),
        id="deadline_reminders",
        name="Send deadline reminders",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started successfully",
        jobs=[job.id for job in _scheduler.get_jobs()],
    )


def start_scheduler() -> None:
    """Initialize and start the APScheduler. Wrapper for sync calling."""
    # Spawn background startup task
    asyncio.create_task(start_scheduler_async())


async def shutdown_scheduler_async() -> None:
    """Async shutdown helper."""
    global _scheduler, _lock_refresh_task, _redis_client
    
    # Stop scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler shutdown")

    # Cancel lock refresh task
    if _lock_refresh_task:
        _lock_refresh_task.cancel()
        try:
            await _lock_refresh_task
        except asyncio.CancelledError:
            pass
        _lock_refresh_task = None

    # Release lock
    if _redis_client:
        try:
            await release_lock(_redis_client)
            await _redis_client.close()
        except Exception as e:
            logger.error("Error releasing scheduler lock during shutdown", error=str(e))
        finally:
            _redis_client = None


def shutdown_scheduler() -> None:
    """Gracefully shutdown the scheduler."""
    asyncio.create_task(shutdown_scheduler_async())


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the scheduler instance."""
    return _scheduler


async def get_scheduler_status_details() -> dict:
    """Get current status of the scheduler and lock state."""
    global _redis_client
    
    is_running = _scheduler is not None and _scheduler.running
    status = "disabled" if not settings.scheduler_should_run else ("active" if is_running else "standby")
    
    lock_owner = None
    lock_ttl = -1
    
    if _redis_client:
        lock_owner, lock_ttl = await get_lock_info(_redis_client)
    else:
        # Check lock info independently
        try:
            temp_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            lock_owner, lock_ttl = await get_lock_info(temp_redis)
            await temp_redis.close()
        except Exception:
            pass

    return {
        "status": status,
        "is_running": is_running,
        "lock_owner": lock_owner,
        "lock_ttl": lock_ttl,
        "enabled_in_config": settings.SCHEDULER_ENABLED,
        "timezone": settings.SCHEDULER_TIMEZONE,
    }
