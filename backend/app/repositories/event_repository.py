"""Event repository with search, filter, and vector similarity queries."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.other import SavedEvent
from app.repositories.base import BaseRepository
from app.schemas.schemas import EventFilter


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[EventFilter] = None,
        user_id: Optional[uuid.UUID] = None,
        sort_by: str = "ai_score",
    ) -> Tuple[List[Event], int]:
        """Get paginated events with optional filters."""
        query = select(Event).where(Event.is_active == True)

        if filters:
            query = self._apply_filters(query, filters)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Sort
        sort_col = getattr(Event, sort_by, Event.ai_score)
        query = query.order_by(desc(sort_col))

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        return events, total

    def _apply_filters(self, query, filters: EventFilter):
        """Apply EventFilter to a query."""
        if filters.platform:
            query = query.where(Event.platform.in_(filters.platform))
        if filters.event_type:
            query = query.where(Event.event_type.in_(filters.event_type))
        if filters.is_remote is not None:
            query = query.where(Event.is_remote == filters.is_remote)
        if filters.is_free is not None:
            query = query.where(Event.is_free == filters.is_free)
        if filters.deadline_before:
            query = query.where(Event.registration_deadline <= filters.deadline_before)
        if filters.deadline_after:
            query = query.where(Event.registration_deadline >= filters.deadline_after)
        if filters.min_score:
            query = query.where(Event.ai_score >= filters.min_score)
        return query

    async def keyword_search(
        self, query_str: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Event], int]:
        """Full-text keyword search on title and description."""
        search_filter = or_(
            Event.title.ilike(f"%{query_str}%"),
            Event.description.ilike(f"%{query_str}%"),
            Event.tags.any(query_str.lower()),  # type: ignore
            Event.organizer.ilike(f"%{query_str}%"),
        )
        query = select(Event).where(and_(Event.is_active == True, search_filter))

        total = (await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar_one()

        query = query.order_by(desc(Event.ai_score))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def semantic_search(
        self, embedding: List[float], limit: int = 20
    ) -> List[Event]:
        """Vector similarity search using pgvector cosine distance."""
        from sqlalchemy import text
        query = text("""
            SELECT id FROM events
            WHERE is_active = true AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """)
        result = await self.db.execute(query, {"embedding": embedding, "limit": limit})
        ids = [row[0] for row in result.fetchall()]

        if not ids:
            return []

        events_result = await self.db.execute(
            select(Event).where(Event.id.in_(ids))
        )
        events = list(events_result.scalars().all())
        # Preserve order from vector search
        event_map = {e.id: e for e in events}
        return [event_map[id_] for id_ in ids if id_ in event_map]

    async def get_upcoming_deadlines(self, days: int = 7) -> List[Event]:
        """Get events with deadlines in the next N days."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=days)
        result = await self.db.execute(
            select(Event)
            .where(
                and_(
                    Event.is_active == True,
                    Event.registration_deadline >= now,
                    Event.registration_deadline <= deadline,
                )
            )
            .order_by(Event.registration_deadline)
        )
        return list(result.scalars().all())

    async def get_by_platform(self, platform: str) -> List[Event]:
        result = await self.db.execute(
            select(Event).where(and_(Event.platform == platform, Event.is_active == True))
        )
        return list(result.scalars().all())

    async def get_by_content_hash(self, content_hash: str) -> Optional[Event]:
        result = await self.db.execute(
            select(Event).where(Event.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def get_today_events(self) -> List[Event]:
        """Events crawled today."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(Event)
            .where(and_(Event.is_active == True, Event.crawled_at >= today_start))
            .order_by(desc(Event.ai_score))
            .limit(50)
        )
        return list(result.scalars().all())

    async def is_saved_by_user(self, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(SavedEvent).where(
                and_(SavedEvent.event_id == event_id, SavedEvent.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_saved_events(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Event], int]:
        saved_ids_query = select(SavedEvent.event_id).where(SavedEvent.user_id == user_id)
        query = select(Event).where(Event.id.in_(saved_ids_query))
        total = (await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar_one()
        query = query.order_by(desc(Event.ai_score)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
