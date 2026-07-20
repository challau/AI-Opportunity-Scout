"""Admin API — dashboard stats, crawler management."""

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_db
from app.models.event import Event
from app.models.other import CrawlerLog, Notification
from app.models.user import User
from app.schemas.schemas import AdminStats, CrawlerLogResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get admin dashboard statistics."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_events = (await db.execute(select(func.count()).select_from(Event))).scalar_one()
    total_notifications = (await db.execute(select(func.count()).select_from(Notification))).scalar_one()
    events_today = (await db.execute(
        select(func.count()).select_from(Event).where(Event.crawled_at >= today)
    )).scalar_one()

    # Latest crawler log
    last_log_result = await db.execute(
        select(CrawlerLog).order_by(CrawlerLog.started_at.desc()).limit(1)
    )
    last_log = last_log_result.scalar_one_or_none()

    return AdminStats(
        total_users=total_users,
        total_events=total_events,
        total_notifications=total_notifications,
        events_today=events_today,
        active_crawlers=0,
        last_crawl_at=last_log.started_at if last_log else None,
    )


@router.get("/crawler-logs", response_model=list[CrawlerLogResponse])
async def get_crawler_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get crawler execution logs."""
    query = select(CrawlerLog).order_by(CrawlerLog.started_at.desc())
    if platform:
        query = query.where(CrawlerLog.platform == platform)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/users", response_model=list)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all users (admin only)."""
    from app.schemas.schemas import UserResponse
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    users = list(result.scalars().all())
    return [UserResponse.model_validate(u) for u in users]


@router.get("/analytics/events-by-platform")
async def events_by_platform(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get event count grouped by platform."""
    result = await db.execute(
        select(Event.platform, func.count(Event.id).label("count"))
        .group_by(Event.platform)
        .order_by(func.count(Event.id).desc())
    )
    return [{"platform": row[0], "count": row[1]} for row in result.fetchall()]


@router.get("/analytics/events-by-type")
async def events_by_type(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Get event count grouped by type."""
    result = await db.execute(
        select(Event.event_type, func.count(Event.id).label("count"))
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
    )
    return [{"type": row[0], "count": row[1]} for row in result.fetchall()]
