"""AtCoder contests collector via public API."""

import structlog
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.collectors.base import BaseCollector

logger = structlog.get_logger()


class AtCoderCollector(BaseCollector):
    PLATFORM_NAME = "atcoder"
    BASE_URL = "https://atcoder.jp"

    async def crawl(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        try:
            # AtCoder Problems API (community, not official — but stable)
            async with httpx.AsyncClient(
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Opportunity-Scout/1.0)",
                    "Accept": "application/json",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(
                    "https://kenkoooo.com/atcoder/resources/contests.json",
                )
                resp.raise_for_status()
                contests = resp.json()

                now_ts = datetime.now(timezone.utc).timestamp()

                for c in contests:
                    start_ts = c.get("start_epoch_second", 0)
                    # Only include upcoming/recent (within 60 days from now)
                    if not (now_ts - 86400 <= start_ts <= now_ts + 60 * 86400):
                        continue
                    events.append(self._normalize(c))

                # Limit to 10 most recent
                events = events[:10]

        except Exception as e:
            logger.warning("AtCoder API failed, using fallback mock data", error=str(e))
            events = self._fallback_events()

        logger.info("AtCoder crawl complete", count=len(events))
        return events

    def _normalize(self, raw: dict) -> dict[str, Any]:
        start_ts = raw.get("start_epoch_second", 0)
        duration_s = raw.get("duration_second", 3600)

        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc) if start_ts else None
        end_dt = datetime.fromtimestamp(start_ts + duration_s, tz=timezone.utc) if start_ts else None

        contest_id = raw.get("id", "")
        title = raw.get("title", contest_id) or contest_id

        return {
            "title": title,
            "description": f"AtCoder programming contest: {title}",
            "platform": self.PLATFORM_NAME,
            "event_type": "coding_contest",
            "tags": ["competitive-programming", "atcoder"],
            "domains": ["Competitive Programming"],
            "is_remote": True,
            "is_free": True,
            "registration_url": f"https://atcoder.jp/contests/{contest_id}" if contest_id else "https://atcoder.jp/contests/",
            "event_start_date": start_dt,
            "event_end_date": end_dt,
            "registration_deadline": start_dt,
        }

    def _fallback_events(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "title": "AtCoder Beginner Contest (ABC)",
                "description": "Weekly AtCoder Beginner Contest — perfect for newcomers to competitive programming.",
                "platform": self.PLATFORM_NAME,
                "event_type": "coding_contest",
                "tags": ["competitive-programming", "atcoder", "beginner"],
                "domains": ["Competitive Programming"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://atcoder.jp/contests/",
                "event_start_date": now + timedelta(days=4),
                "event_end_date": now + timedelta(days=4, hours=2),
                "registration_deadline": now + timedelta(days=4),
            },
            {
                "title": "AtCoder Regular Contest (ARC)",
                "description": "AtCoder Regular Contest — mid-difficulty competitive programming contest.",
                "platform": self.PLATFORM_NAME,
                "event_type": "coding_contest",
                "tags": ["competitive-programming", "atcoder", "regular"],
                "domains": ["Competitive Programming"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://atcoder.jp/contests/",
                "event_start_date": now + timedelta(days=11),
                "event_end_date": now + timedelta(days=11, hours=2),
                "registration_deadline": now + timedelta(days=11),
            },
        ]
