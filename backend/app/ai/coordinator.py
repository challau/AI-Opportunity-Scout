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

        # Build user context — query the profile explicitly (accessing
        # user.profile would lazy-load outside the async greenlet and crash)
        profile_info = "No profile configured"
        try:
            from sqlalchemy import select
            from app.models.profile import UserProfile
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            p = result.scalar_one_or_none()
            if p:
                profile_info = f"""
                Interests: {', '.join(p.interested_domains or [])}
                Languages: {', '.join(p.programming_languages or [])}
                Country: {p.country or 'Not specified'}
                """
        except Exception as e:
            logger.warning("Could not load profile for chat context", error=str(e))

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
        if any(kw in message.lower() for kw in ["find", "show", "hackathon", "contest", "internship", "recommend", "opportunit", "event"]):
            # Search meaningful keywords, not the raw sentence — a full
            # sentence never matches as one ILIKE substring
            stopwords = {
                "find", "show", "me", "a", "an", "the", "with", "for", "in", "on",
                "of", "to", "any", "some", "all", "new", "latest", "upcoming",
                "recommend", "please", "list", "give", "get", "what", "which",
                "are", "is", "there", "money", "and", "or",
            }
            keywords = [w for w in message.lower().split() if w.strip("?.,!") not in stopwords]
            seen_ids = set()
            events = []
            for kw in (keywords or ["hackathon"])[:4]:
                found, _ = await repo.keyword_search(
                    query_str=kw.strip("?.,!"),
                    page=1,
                    page_size=5,
                )
                for e in found:
                    if e.id not in seen_ids:
                        seen_ids.add(e.id)
                        events.append(e)
                if len(events) >= 5:
                    break
            suggested_events = [EventResponse.model_validate(e) for e in events[:5]]

            if suggested_events:
                event_context = "\n".join([
                    f"- {e.title} ({e.platform}) - Deadline: {e.registration_deadline}"
                    for e in suggested_events
                ])
                messages[-1]["content"] += f"\n\nRelevant events I found:\n{event_context}"

        response = None
        openai_configured = bool(
            settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your")
        )
        if openai_configured:
            try:
                response = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,  # type: ignore
                    max_tokens=1000,
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning("OpenAI chat failed, falling back to search-only reply", error=str(e))

        if response:
            reply = response.choices[0].message.content or ""
        elif suggested_events:
            listing = "\n".join(
                f"• {e.title} ({e.platform})" for e in suggested_events
            )
            reply = (
                "Here are opportunities matching your search:\n\n"
                f"{listing}\n\n"
                "(AI answers are unavailable right now, but these matched your query.)"
            )
        else:
            reply = (
                "I searched the database but couldn't find matching events for that. "
                "Try keywords like 'hackathon', 'contest', or a platform name. "
                "(AI answers are unavailable right now.)"
            )

        return ChatResponse(
            message=reply,
            suggested_events=suggested_events,
            metadata={"model": settings.OPENAI_MODEL if response else "search-fallback"},
        )
