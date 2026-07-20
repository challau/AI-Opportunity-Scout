"""Recommendation service — personalized event recommendations."""

from typing import List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.profile import UserProfile
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger()


class RecommendationService:
    """Generates personalized event recommendations based on user profile."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def get_recommendations(
        self,
        user: User,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[Event]:
        """Get personalized recommendations for a user."""
        # Load user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile or not any([
            profile.interested_domains,
            profile.programming_languages,
        ]):
            # No profile — return top-ranked events
            repo = EventRepository(db)
            events, _ = await repo.get_paginated(1, limit, sort_by="ai_score")
            return events

        # Build interest query text
        interest_text = " ".join([
            " ".join(profile.interested_domains or []),
            " ".join(profile.programming_languages or []),
            " ".join(profile.preferred_platforms or []),
        ]).strip()

        # Semantic search based on interests
        embedding = await self.embedding_service.get_embedding(interest_text)
        repo = EventRepository(db)
        events = await repo.semantic_search(embedding, limit=limit * 2)

        # Filter by preferred platforms if set
        if profile.preferred_platforms:
            preferred = [p.lower() for p in profile.preferred_platforms]
            filtered = [e for e in events if e.platform.lower() in preferred]
            # Fall back to all if filtering removes too many
            if len(filtered) >= limit // 2:
                events = filtered

        return events[:limit]
