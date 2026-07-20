"""Summarizer Agent — generates concise AI summaries for events."""

import asyncio
from typing import Dict

import structlog
from openai import AsyncOpenAI

from app.ai.prompts import SUMMARIZER_PROMPT
from app.core.config import settings

logger = structlog.get_logger()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def _summarize_single(event: Dict) -> str:
    """Generate a 2-3 sentence AI summary for one event."""
    try:
        prompt = SUMMARIZER_PROMPT.format(
            title=event.get("title", ""),
            description=(event.get("description", "") or "")[:1000],
            platform=event.get("platform", ""),
            event_type=event.get("event_type", ""),
            prize=event.get("prize", "Not specified"),
            deadline=event.get("deadline") or event.get("registration_deadline", "Not specified"),
            eligibility=event.get("eligibility", "Open to all"),
        )
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.6,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception as e:
        logger.warning("Summarization failed", error=str(e))
        return event.get("description", "")[:200] if event.get("description") else ""


async def summarize_events(state: Dict) -> Dict:
    """Generate AI summaries for all ranked events in batches."""
    events = state["ranked_events"]

    if not events:
        return {**state, "summarized_events": []}

    # Batch summarize with concurrency limit
    BATCH_SIZE = 10
    summarized = []

    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i : i + BATCH_SIZE]
        summaries = await asyncio.gather(*[_summarize_single(e) for e in batch])
        for event, summary in zip(batch, summaries):
            event["short_summary"] = summary
            summarized.append(event)

    logger.info("Summarization complete", events=len(summarized))
    return {**state, "summarized_events": summarized}
