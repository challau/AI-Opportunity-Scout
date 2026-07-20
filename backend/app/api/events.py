"""Events API — list, detail, save, unsave."""

import uuid
import math
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_optional_user
from app.models.other import SavedEvent
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.schemas.schemas import EventFilter, EventListResponse, EventResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    is_remote: Optional[bool] = Query(None),
    is_free: Optional[bool] = Query(None),
    sort_by: str = Query("ai_score"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """List events with optional filters and pagination."""
    filters = EventFilter(
        platform=[platform] if platform else None,
        event_type=[event_type] if event_type else None,
        is_remote=is_remote,
        is_free=is_free,
    )

    repo = EventRepository(db)
    events, total = await repo.get_paginated(page, page_size, filters, sort_by=sort_by)

    # Annotate saved status
    event_responses = []
    for event in events:
        er = EventResponse.model_validate(event)
        if current_user:
            er.is_saved = await repo.is_saved_by_user(event.id, current_user.id)
        event_responses.append(er)

    return EventListResponse(
        items=event_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/today", response_model=list[EventResponse])
async def get_today_events(db: AsyncSession = Depends(get_db)):
    """Get events discovered today."""
    repo = EventRepository(db)
    return await repo.get_today_events()


@router.get("/upcoming-deadlines", response_model=list[EventResponse])
async def get_upcoming_deadlines(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Get events with deadlines in the next N days."""
    repo = EventRepository(db)
    return await repo.get_upcoming_deadlines(days)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get event details by ID."""
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    er = EventResponse.model_validate(event)
    if current_user:
        er.is_saved = await repo.is_saved_by_user(event.id, current_user.id)
    return er


@router.post("/{event_id}/save", status_code=status.HTTP_201_CREATED)
async def save_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save an event to user's collection."""
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    already_saved = await repo.is_saved_by_user(event_id, current_user.id)
    if already_saved:
        raise HTTPException(status_code=400, detail="Event already saved")

    saved = SavedEvent(user_id=current_user.id, event_id=event_id)
    db.add(saved)
    await db.commit()
    return {"message": "Event saved"}


@router.delete("/{event_id}/save")
async def unsave_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove event from saved collection."""
    from sqlalchemy import select, and_
    result = await db.execute(
        select(SavedEvent).where(
            and_(SavedEvent.event_id == event_id, SavedEvent.user_id == current_user.id)
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Event not in saved list")

    await db.delete(saved)
    await db.commit()
    return {"message": "Event removed from saved"}


@router.get("/saved/me", response_model=EventListResponse)
async def get_saved_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's saved events."""
    repo = EventRepository(db)
    events, total = await repo.get_user_saved_events(current_user.id, page, page_size)
    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )
