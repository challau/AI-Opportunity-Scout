"""LeetCode contest crawler using the public GraphQL API."""

from datetime import datetime, timezone
from typing import Dict, List

import httpx
import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()

GRAPHQL_URL = "https://leetcode.com/graphql"
CONTEST_QUERY = """
query upcomingContests {
  upcomingContests {
    title
    titleSlug
    startTime
    duration
  }
}
"""


class LeetCodeCrawler(BaseCrawler):
    PLATFORM_NAME = "leetcode"
    BASE_URL = "https://leetcode.com/contest/"

    async def _fetch_events(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(
                headers={**self._get_headers(), "Content-Type": "application/json"},
                timeout=self.timeout,
            ) as client:
                resp = await client.post(
                    GRAPHQL_URL,
                    json={"query": CONTEST_QUERY, "operationName": "upcomingContests"},
                )
                resp.raise_for_status()
                contests = resp.json().get("data", {}).get("upcomingContests", []) or []
            return [self._parse(c) for c in contests[:20]]
        except Exception as e:
            logger.error("LeetCode crawl failed", error=str(e))
            return []

    def _parse(self, c: Dict) -> Dict:
        start_ts = c.get("startTime")
        duration = c.get("duration", 0) or 0
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc) if start_ts else None
        end_dt = (
            datetime.fromtimestamp(start_ts + duration, tz=timezone.utc)
            if start_ts
            else None
        )
        slug = c.get("titleSlug", "")
        return {
            "title": c.get("title", ""),
            "description": f"LeetCode contest - Duration: {duration // 60} minutes",
            "platform": self.PLATFORM_NAME,
            "event_type": "contest",
            "registration_deadline": start_dt,
            "event_start_date": start_dt,
            "event_end_date": end_dt,
            "registration_url": f"https://leetcode.com/contest/{slug}",
            "is_remote": True,
            "is_free": True,
            "prize": None,
            "tags": ["competitive programming", "algorithms", "data structures"],
            "external_id": slug,
        }
