"""LangGraph AI Coordinator — orchestrates the full agent pipeline."""

from typing import Any, Dict, List, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import CHATBOT_SYSTEM
from app.core.config import settings
from app.schemas.schemas import ChatMessage, ChatResponse

logger = structlog.get_logger()


class PipelineState(TypedDict):
    """State passed between agents in the pipeline."""
    raw_events: List[Dict]
    normalized_events: List[Dict]
    deduplicated_events: List[Dict]
    ranked_events: List[Dict]
    summarized_events: List[Dict]
    errors: List[str]
    platform: str
    stats: Dict[str, Any]


class AICoordinator:
    """
    Coordinates the full AI agent pipeline using LangGraph.
    
    Pipeline: Crawler → Normalizer → Dedup → Embeddings → Ranking → Summary → Notifications
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph agent workflow."""
        from app.ai.normalizer_agent import normalize_events
        from app.ai.duplicate_agent import deduplicate_events
        from app.ai.ranking_agent import rank_events
        from app.ai.summarizer_agent import summarize_events

        graph = StateGraph(PipelineState)

        graph.add_node("normalize", normalize_events)
        graph.add_node("deduplicate", deduplicate_events)
        graph.add_node("rank", rank_events)
        graph.add_node("summarize", summarize_events)

        graph.set_entry_point("normalize")
        graph.add_edge("normalize", "deduplicate")
        graph.add_edge("deduplicate", "rank")
        graph.add_edge("rank", "summarize")
        graph.add_edge("summarize", END)

        return graph.compile()

    async def run_pipeline(
        self,
        raw_events: List[Dict],
        platform: str,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Run the full AI processing pipeline on raw crawled events."""
        logger.info("Starting AI pipeline", platform=platform, events_count=len(raw_events))

        initial_state: PipelineState = {
            "raw_events": raw_events,
            "normalized_events": [],
            "deduplicated_events": [],
            "ranked_events": [],
            "summarized_events": [],
            "errors": [],
            "platform": platform,
            "stats": {},
        }

        try:
            result = await self.graph.ainvoke(initial_state)
            logger.info(
                "Pipeline complete",
                platform=platform,
                processed=len(result.get("summarized_events", [])),
            )
            return result
        except Exception as e:
            logger.error("Pipeline failed", platform=platform, error=str(e))
            return {**initial_state, "errors": [str(e)]}

    async def chat(
        self,
        message: str,
        history: List[ChatMessage],
        user: Any,
        db: AsyncSession,
    ) -> ChatResponse:
        """AI chatbot for opportunity discovery."""
        from openai import AsyncOpenAI
        from app.repositories.event_repository import EventRepository
        from app.schemas.schemas import EventResponse

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Build user context
        profile_info = "No profile configured"
        if hasattr(user, "profile") and user.profile:
            p = user.profile
            profile_info = f"""
            Interests: {', '.join(p.interested_domains or [])}
            Languages: {', '.join(p.programming_languages or [])}
            Country: {p.country or 'Not specified'}
            """

        # Get event count
        repo = EventRepository(db)
        event_count = await repo.count()

        system_prompt = CHATBOT_SYSTEM.format(
            user_profile=profile_info,
            event_count=event_count,
        )

        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})

        # Check if user is asking for specific events
        suggested_events = []
        if any(kw in message.lower() for kw in ["find", "show", "hackathon", "contest", "internship", "recommend"]):
            events, _ = await repo.keyword_search(
                query_str=message,
                page=1,
                page_size=5,
            )
            suggested_events = [EventResponse.model_validate(e) for e in events]

            if suggested_events:
                event_context = "\n".join([
                    f"- {e.title} ({e.platform}) - Deadline: {e.registration_deadline}"
                    for e in suggested_events
                ])
                messages[-1]["content"] += f"\n\nRelevant events I found:\n{event_context}"

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,  # type: ignore
            max_tokens=1000,
            temperature=0.7,
        )

        reply = response.choices[0].message.content or ""

        return ChatResponse(
            message=reply,
            suggested_events=suggested_events,
            metadata={"model": settings.OPENAI_MODEL},
        )
