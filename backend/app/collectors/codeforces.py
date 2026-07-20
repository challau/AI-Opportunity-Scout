"""Codeforces, CodeChef, AtCoder crawlers."""

from datetime import datetime, timezone
from typing import Dict, List

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class CodeforcesCrawler(BaseCrawler):
    PLATFORM_NAME = "codeforces"
    API_URL = "https://codeforces.com/api/contest.list"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL)
            if data.get("status") != "OK":
                return []
            contests = data.get("result", [])
            # Filter upcoming
            upcoming = [c for c in contests if c.get("phase") in ["BEFORE", "CODING"]]
            return [self._parse(c) for c in upcoming[:30]]
        except Exception as e:
            logger.error("Codeforces crawl failed", error=str(e))
            return []

    def _parse(self, c: Dict) -> Dict:
        start_ts = c.get("startTimeSeconds")
        duration = c.get("durationSeconds", 0)
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc) if start_ts else None
        end_dt = datetime.fromtimestamp(start_ts + duration, tz=timezone.utc) if start_ts else None

        return {
            "title": c.get("name", ""),
            "description": f"Codeforces round - Type: {c.get('type', 'CF')}",
            "platform": self.PLATFORM_NAME,
            "event_type": "contest",
            "registration_deadline": start_dt,
            "event_start_date": start_dt,
            "event_end_date": end_dt,
            "registration_url": f"https://codeforces.com/contests/{c.get('id')}",
            "is_remote": True,
            "is_free": True,
            "prize": None,
            "tags": ["competitive programming", "algorithms"],
            "external_id": str(c.get("id", "")),
        }


class CodeChefCrawler(BaseCrawler):
    PLATFORM_NAME = "codechef"
    API_URL = "https://www.codechef.com/api/list/contests/all"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL, {"sort_by": "START", "sorting_order": "asc"})
            contests = (
                data.get("present_contests", []) +
                data.get("future_contests", [])
            )
            return [self._parse(c) for c in contests[:30]]
        except Exception as e:
            logger.error("CodeChef crawl failed", error=str(e))
            return []

    def _parse(self, c: Dict) -> Dict:
        return {
            "title": c.get("contest_name", ""),
            "description": f"CodeChef Contest - Duration: {c.get('contest_duration', '')} minutes",
            "platform": self.PLATFORM_NAME,
            "event_type": "contest",
            "registration_deadline": c.get("contest_start_date_iso"),
            "event_start_date": c.get("contest_start_date_iso"),
            "event_end_date": c.get("contest_end_date_iso"),
            "registration_url": f"https://www.codechef.com/{c.get('contest_code', '')}",
            "is_remote": True,
            "is_free": True,
            "prize": c.get("prize_pool_amount"),
            "tags": ["competitive programming", "algorithms", "data structures"],
            "external_id": c.get("contest_code", ""),
        }


class AtCoderCrawler(BaseCrawler):
    PLATFORM_NAME = "atcoder"
    API_URL = "https://atcoder.jp/contests/"

    async def _fetch_events(self) -> List[Dict]:
        """Scrape AtCoder upcoming contests."""
        try:
            from bs4 import BeautifulSoup  # type: ignore
            resp = await self._get(self.API_URL)
            soup = BeautifulSoup(resp.text, "lxml")

            upcoming_table = soup.find("div", {"id": "contest-table-upcoming"})
            if not upcoming_table:
                return []

            events = []
            rows = upcoming_table.find_all("tr")[1:]  # Skip header
            for row in rows[:20]:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue
                start_str = cols[0].get_text(strip=True)
                name_link = cols[1].find("a")
                if not name_link:
                    continue
                slug = name_link.get("href", "").lstrip("/contests/")
                events.append({
                    "title": name_link.get_text(strip=True),
                    "description": f"AtCoder contest - Duration: {cols[2].get_text(strip=True)}",
                    "platform": self.PLATFORM_NAME,
                    "event_type": "contest",
                    "registration_deadline": start_str,
                    "registration_url": f"https://atcoder.jp/contests/{slug}",
                    "is_remote": True,
                    "is_free": True,
                    "prize": cols[3].get_text(strip=True) if len(cols) > 3 else None,
                    "tags": ["competitive programming", "algorithms"],
                    "external_id": slug,
                })
            return events
        except Exception as e:
            logger.error("AtCoder crawl failed", error=str(e))
            return []
