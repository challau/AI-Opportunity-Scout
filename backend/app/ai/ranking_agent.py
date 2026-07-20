"""Ranking Agent — scores events using heuristics and AI."""

from datetime import datetime, timezone
from typing import Dict

import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Platform prestige scores
PLATFORM_SCORES = {
    "google": 90, "microsoft": 85, "mlh": 80, "kaggle": 75,
    "devpost": 70, "unstop": 65, "devfolio": 65, "hackerearth": 60,
    "codeforces": 75, "codechef": 65, "atcoder": 70,
    "hack2skill": 55, "ieee": 70, "gsoc": 95, "gssoc": 70,
    "github": 80,
}

EVENT_TYPE_SCORES = {
    "open_source": 85, "competition": 80, "hackathon": 75,
    "internship": 90, "hiring": 85, "workshop": 60,
    "contest": 70, "quiz": 50, "conference": 65,
}


def _compute_heuristic_score(event: Dict) -> float:
    """Compute a heuristic-based score 0-100."""
    score = 50.0  # Base score

    # Platform bonus
    platform = event.get("platform", "").lower()
    score += (PLATFORM_SCORES.get(platform, 50) - 50) * 0.3

    # Event type bonus
    event_type = event.get("event_type", "hackathon").lower()
    score += (EVENT_TYPE_SCORES.get(event_type, 60) - 60) * 0.2

    # Prize bonus
    prize_amount = event.get("prize_amount") or 0
    if prize_amount > 10000:
        score += 15
    elif prize_amount > 5000:
        score += 10
    elif prize_amount > 1000:
        score += 5
    elif event.get("prize"):
        score += 3

    # Deadline urgency (events soon get slight boost)
    deadline = event.get("deadline") or event.get("registration_deadline")
    if deadline:
        try:
            if isinstance(deadline, str):
                deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            else:
                deadline_dt = deadline
            now = datetime.now(timezone.utc)
            days_left = (deadline_dt - now).days
            if 3 <= days_left <= 14:
                score += 5  # Boost upcoming deadlines
            elif days_left < 0:
                score -= 30  # Penalize expired
        except (ValueError, TypeError):
            pass

    # Free event bonus
    if event.get("is_free", True):
        score += 3

    # Remote bonus
    if event.get("is_remote", False):
        score += 5

    return max(0.0, min(100.0, score))


async def rank_events(state: Dict) -> Dict:
    """Rank events using heuristics (fast) with optional AI enhancement."""
    events = state["deduplicated_events"]
    ranked = []

    for event in events:
        score = _compute_heuristic_score(event)
        event["ai_score"] = round(score, 2)
        ranked.append(event)

    # Sort by score descending
    ranked.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    logger.info("Ranking complete", events=len(ranked))
    return {**state, "ranked_events": ranked}
