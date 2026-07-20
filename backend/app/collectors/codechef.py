"""CodeChef contests collector via public API."""

import structlog
from datetime import datetime, timezone
from typing import Any

import httpx

from app.collectors.base import BaseCollector

logger = structlog.get_logger()


class CodeChefCollector(BaseCollector):
    PLATFORM_NAME = "codechef"
    BASE_URL = "https://www.codechef.com"

    async def crawl(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Opportunity-Scout/1.0)",
                    "Accept": "application/json",
                },
                follow_redirects=True,
            ) as client:
                # CodeChef public contests API
                resp = await client.get(
                    "https://www.codechef.com/api/list/contests/all",
                    params={"sort_by": "START", "sorting_order": "asc", "offset": 0, "mode": "all"},
                )
                resp.raise_for_status()
                data = resp.json()

                for section in ("present_contests", "future_contests"):
                    contests = data.get(section, [])
                    for c in contests:
                        events.append(self._normalize(c))

        except Exception as e:
            logger.warning("CodeChef API failed, using fallback mock data", error=str(e))
            events = self._fallback_events()

        logger.info("CodeChef crawl complete", count=len(events))
        return events

    def _normalize(self, raw: dict) -> dict[str, Any]:
        start_str = raw.get("contest_start_date", "") or raw.get("contest_start_date_iso", "")
        end_str = raw.get("contest_end_date", "") or raw.get("contest_end_date_iso", "")

        start_dt = self._parse_dt(start_str)
        end_dt = self._parse_dt(end_str)

        code = raw.get("contest_code", "")
        title = raw.get("contest_name", code) or code

        return {
            "title": title,
            "description": f"CodeChef contest: {title}",
            "platform": self.PLATFORM_NAME,
            "event_type": "coding_contest",
            "tags": ["competitive-programming", "codechef"],
            "domains": ["Competitive Programming"],
            "is_remote": True,
            "is_free": True,
            "registration_url": f"https://www.codechef.com/{code}" if code else "https://www.codechef.com/contests",
            "event_start_date": start_dt,
            "event_end_date": end_dt,
            "registration_deadline": start_dt,
        }

    def _parse_dt(self, s: str):
        if not s:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(s.strip(), fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        return None

    def _fallback_events(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        return [
            {
                "title": "CodeChef Starters (Weekly)",
                "description": "Weekly competitive programming contest on CodeChef for all levels.",
                "platform": self.PLATFORM_NAME,
                "event_type": "coding_contest",
                "tags": ["competitive-programming", "codechef"],
                "domains": ["Competitive Programming"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://www.codechef.com/contests",
                "event_start_date": now + timedelta(days=3),
                "event_end_date": now + timedelta(days=3, hours=2),
                "registration_deadline": now + timedelta(days=3),
            },
            {
                "title": "CodeChef Long Challenge (Monthly)",
                "description": "Monthly long competitive programming challenge on CodeChef.",
                "platform": self.PLATFORM_NAME,
                "event_type": "coding_contest",
                "tags": ["competitive-programming", "codechef", "long-challenge"],
                "domains": ["Competitive Programming"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://www.codechef.com/contests",
                "event_start_date": now + timedelta(days=7),
                "event_end_date": now + timedelta(days=17),
                "registration_deadline": now + timedelta(days=7),
            },
        ]
