"""Admin Scheduler API router for monitoring and manually triggering background jobs."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.deps import get_current_admin, get_db
from app.models.user import User
from app.models.other import SchedulerLog
from app.scheduler.scheduler import get_scheduler, get_scheduler_status_details
from app.scheduler.tasks import run_crawl_task, run_daily_digest, run_deadline_reminders

logger = structlog.get_logger()
router = APIRouter(prefix="/scheduler", tags=["Scheduler Management"])


@router.get("/status")
async def get_scheduler_status(
    _: User = Depends(get_current_admin),
):
    """Get active status and Redis locking information of the scheduler."""
    details = await get_scheduler_status_details()
    return details


@router.get("/jobs")
async def get_scheduler_jobs(
    _: User = Depends(get_current_admin),
):
    """List all registered scheduler jobs with their next run times."""
    scheduler = get_scheduler()
    if not scheduler:
        return {"jobs": [], "message": "Scheduler is not running on this instance."}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return {"jobs": jobs}


@router.post("/trigger/{job_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scheduler_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Manually trigger a background scheduler job by ID."""
    scheduler = get_scheduler()

    # Define tasks mapping
    tasks = {
        "crawl_all": lambda: run_crawl_task("all", "manual"),
        "daily_digest": lambda: run_daily_digest("manual"),
        "deadline_reminders": lambda: run_deadline_reminders("manual"),
    }

    if job_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job ID. Supported: {', '.join(tasks.keys())}"
        )

    # Execute task in background safely without blocking
    import asyncio
    asyncio.create_task(tasks[job_id]())

    logger.info("Scheduler job manually triggered", job_id=job_id)
    return {"message": f"Job '{job_id}' successfully triggered in background."}


@router.get("/logs")
async def get_scheduler_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get a paginated history of scheduler job runs and metrics."""
    # Build query
    query = select(SchedulerLog).order_by(SchedulerLog.started_at.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Offset & limit pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    logs = list(result.scalars().all())

    # Map to list of dicts to render JSON properly
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": str(log.id),
            "job_id": log.job_id,
            "job_name": log.job_name,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": log.duration_seconds,
            "error_message": log.error_message,
            "platforms_crawled": log.platforms_crawled,
            "events_found": log.events_found,
            "events_new": log.events_new,
            "emails_sent": log.emails_sent,
            "telegrams_sent": log.telegrams_sent,
            "failures": log.failures,
            "retry_count": log.retry_count,
            "trigger_source": log.trigger_source,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": logs_data
    }
