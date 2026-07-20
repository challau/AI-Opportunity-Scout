"""Search API — keyword, semantic, and AI-powered search."""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_optional_user
from app.repositories.event_repository import EventRepository
from app.schemas.schemas import SearchRequest, SearchResponse, EventResponse
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger()
router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Search events using keyword, semantic, or hybrid search."""
    repo = EventRepository(db)
    ai_explanation = None

    if payload.search_type == "keyword":
        events, total = await repo.keyword_search(payload.query, payload.page, payload.page_size)

    elif payload.search_type == "semantic":
        embedding_service = EmbeddingService()
        embedding = await embedding_service.get_embedding(payload.query)
        events = await repo.semantic_search(embedding, limit=payload.page_size)
        total = len(events)

    elif payload.search_type == "hybrid":
        # Combine keyword and semantic
        kw_events, kw_total = await repo.keyword_search(payload.query, 1, 50)
        embedding_service = EmbeddingService()
        embedding = await embedding_service.get_embedding(payload.query)
        sem_events = await repo.semantic_search(embedding, limit=50)

        # Merge and deduplicate by ID
        seen = set()
        events = []
        for e in kw_events + sem_events:
            if e.id not in seen:
                seen.add(e.id)
                events.append(e)

        # Sort by AI score
        events.sort(key=lambda x: x.ai_score, reverse=True)
        total = len(events)
        events = events[(payload.page - 1) * payload.page_size : payload.page * payload.page_size]

    elif payload.search_type == "ai":
        # AI-powered natural language search
        from app.services.search_service import AISearchService
        search_service = AISearchService()
        result = await search_service.ai_search(payload.query, db)
        events = result["events"]
        total = len(events)
        ai_explanation = result.get("explanation")

    else:
        raise HTTPException(status_code=400, detail="Invalid search_type")

    return SearchResponse(
        query=payload.query,
        search_type=payload.search_type,
        results=[EventResponse.model_validate(e) for e in events],
        total=total,
        ai_explanation=ai_explanation,
    )
