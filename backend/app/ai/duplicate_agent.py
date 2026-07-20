"""Duplicate Detection Agent — removes duplicate events."""

import hashlib
from typing import Dict, List, Set

import structlog

logger = structlog.get_logger()


def _compute_content_hash(event: Dict) -> str:
    """Create a hash from event title + platform + url for exact dedup."""
    content = f"{event.get('title', '').lower().strip()}"
    content += f"|{event.get('platform', '').lower()}"
    content += f"|{event.get('registration_url', '').lower()}"
    return hashlib.sha256(content.encode()).hexdigest()


def _title_similarity(t1: str, t2: str) -> float:
    """Simple Jaccard similarity between two titles."""
    w1 = set(t1.lower().split())
    w2 = set(t2.lower().split())
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)


async def deduplicate_events(state: Dict) -> Dict:
    """Remove duplicate events using hash-based and fuzzy matching."""
    events = state["normalized_events"]
    seen_hashes: Set[str] = set()
    unique: List[Dict] = []
    duplicates_removed = 0

    for event in events:
        content_hash = _compute_content_hash(event)
        event["content_hash"] = content_hash

        if content_hash in seen_hashes:
            duplicates_removed += 1
            continue

        # Check title similarity against recent unique events
        is_fuzzy_duplicate = False
        title = event.get("title", "")
        for existing in unique[-50:]:  # Check last 50 events
            if (
                existing.get("platform") == event.get("platform")
                and _title_similarity(title, existing.get("title", "")) > 0.85
            ):
                is_fuzzy_duplicate = True
                duplicates_removed += 1
                break

        if not is_fuzzy_duplicate:
            seen_hashes.add(content_hash)
            unique.append(event)

    logger.info(
        "Deduplication complete",
        input=len(events),
        output=len(unique),
        removed=duplicates_removed,
    )
    return {
        **state,
        "deduplicated_events": unique,
        "stats": {**state.get("stats", {}), "duplicates_removed": duplicates_removed},
    }
