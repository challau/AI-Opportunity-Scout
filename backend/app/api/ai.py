"""AI API — chatbot and recommendations."""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.schemas import ChatRequest, ChatResponse, EventResponse
from app.services.recommendation_service import RecommendationService

logger = structlog.get_logger()
router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI chatbot for opportunity discovery."""
    from app.ai.coordinator import AICoordinator
    coordinator = AICoordinator()
    result = await coordinator.chat(
        message=payload.message,
        history=payload.conversation_history,
        user=current_user,
        db=db,
    )
    return result


@router.get("/recommendations", response_model=list[EventResponse])
async def get_recommendations(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-powered personalized event recommendations."""
    service = RecommendationService()
    events = await service.get_recommendations(current_user, db, limit=limit)
    return [EventResponse.model_validate(e) for e in events]


@router.post("/trigger-crawl")
async def trigger_crawl(
    platform: str = "all",
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a crawl (admin or dev use)."""
    from app.scheduler.tasks import run_crawl_task
    import asyncio
    asyncio.create_task(run_crawl_task(platform))
    return {"message": f"Crawl triggered for platform: {platform}"}
