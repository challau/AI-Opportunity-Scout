"""Normalizer Agent — converts raw crawled data into unified schema."""

import json
from typing import Dict

import structlog
from openai import AsyncOpenAI

from app.ai.prompts import NORMALIZER_PROMPT
from app.core.config import settings

logger = structlog.get_logger()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def normalize_events(state: Dict) -> Dict:
    """Normalize raw event data into unified schema using AI."""
    raw_events = state["raw_events"]
    normalized = []
    errors = list(state.get("errors", []))

    # Check if OpenAI is configured; if not, skip AI normalization entirely
    ai_available = bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your"))

    for raw in raw_events:
        try:
            # Fast path: if already has required fields, just clean it
            if all(k in raw for k in ["title", "registration_url", "platform"]):
                normalized.append(_clean_event(raw))
                continue

            # AI normalization for complex/inconsistent data (if API available)
            if not ai_available:
                # Fallback: best-effort local normalization
                normalized.append(_clean_event(raw))
                continue

            prompt = NORMALIZER_PROMPT.format(raw_data=json.dumps(raw, default=str))
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",  # Use faster model for normalization
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=500,
                    temperature=0,
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("AI normalization returned empty response")
                normalized_data = json.loads(content)
                normalized_data["platform"] = raw.get("platform", normalized_data.get("platform", "unknown"))
                normalized.append(normalized_data)
            except Exception as ai_err:
                # AI failed — fall back to local cleaning
                logger.warning("AI normalization failed, using local fallback", error=str(ai_err))
                normalized.append(_clean_event(raw))

        except Exception as e:
            logger.warning("Failed to normalize event", error=str(e), title=raw.get("title", "?"))
            errors.append(f"Normalization failed: {str(e)}")

    logger.info("Normalization complete", input=len(raw_events), output=len(normalized))
    return {**state, "normalized_events": normalized, "errors": errors}


def _clean_event(raw: Dict) -> Dict:
    """Clean and standardize a well-formatted raw event."""
    return {
        "title": str(raw.get("title", "")).strip(),
        "description": raw.get("description", ""),
        "platform": raw.get("platform", ""),
        "event_type": raw.get("event_type", "hackathon"),
        "prize": raw.get("prize"),
        "prize_amount": raw.get("prize_amount"),
        "deadline": raw.get("deadline") or raw.get("registration_deadline"),
        "event_start_date": raw.get("event_start_date") or raw.get("start_date"),
        "location": raw.get("location"),
        "is_remote": raw.get("is_remote", False),
        "is_free": raw.get("is_free", True),
        "eligibility": raw.get("eligibility"),
        "tags": raw.get("tags", []),
        "domains": raw.get("domains", []),
        "registration_url": raw.get("registration_url") or raw.get("url", ""),
        "image_url": raw.get("image_url"),
        "organizer": raw.get("organizer"),
        "external_id": raw.get("external_id") or raw.get("id"),
    }
