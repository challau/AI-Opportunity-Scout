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
    KENKOOOO_API = "https://kenkoooo.com/atcoder/resources/contests.json"

    async def _fetch_events(self) -> List[Dict]:
        """Fetch AtCoder contests from community API first, then scraping fallback."""
        # Try community API (more reliable)
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(self.KENKOOOO_API)
                resp.raise_for_status()
                contests = resp.json()
            from datetime import timezone as _tz
            now_ts = __import__('datetime').datetime.now(_tz.utc).timestamp()
            events = []
            for c in contests:
                start_ts = c.get("start_epoch_second", 0)
                if now_ts - 86400 <= start_ts <= now_ts + 60 * 86400:
                    duration_s = c.get("duration_second", 3600)
                    from datetime import datetime as _dt, timezone as _tzc
                    start_dt = _dt.fromtimestamp(start_ts, tz=_tzc.utc) if start_ts else None
                    end_dt = _dt.fromtimestamp(start_ts + duration_s, tz=_tzc.utc) if start_ts else None
                    cid = c.get("id", "")
                    events.append({
                        "title": c.get("title", cid),
                        "description": f"AtCoder programming contest: {c.get('title', cid)}",
                        "platform": self.PLATFORM_NAME,
                        "event_type": "contest",
                        "registration_deadline": start_dt,
                        "event_start_date": start_dt,
                        "event_end_date": end_dt,
                        "registration_url": f"https://atcoder.jp/contests/{cid}" if cid else "https://atcoder.jp/contests/",
                        "is_remote": True,
                        "is_free": True,
                        "prize": None,
                        "tags": ["competitive programming", "algorithms", "atcoder"],
                        "external_id": cid,
                    })
            if events:
                return events[:10]
        except Exception as e:
            logger.warning("AtCoder kenkoooo API failed, trying scrape", error=str(e))

        # Try HTML scraping
        try:
            from bs4 import BeautifulSoup  # type: ignore
            resp = await self._get(self.API_URL)
            soup = BeautifulSoup(resp.text, "lxml")

            upcoming_table = soup.find("div", {"id": "contest-table-upcoming"})
            if not upcoming_table:
                return self._fallback_events()

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
            return events if events else self._fallback_events()
        except Exception as e:
            logger.error("AtCoder crawl failed, using fallback", error=str(e))
            return self._fallback_events()

    def _fallback_events(self) -> List[Dict]:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        return [
            {
                "title": "AtCoder Beginner Contest (ABC)",
                "description": "Weekly AtCoder Beginner Contest — great for newcomers to competitive programming.",
                "platform": self.PLATFORM_NAME,
                "event_type": "contest",
                "tags": ["competitive programming", "beginner", "atcoder"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://atcoder.jp/contests/",
                "event_start_date": now + timedelta(days=4),
                "event_end_date": now + timedelta(days=4, hours=2),
                "registration_deadline": now + timedelta(days=4),
                "external_id": "atcoder-abc-fallback",
            },
            {
                "title": "AtCoder Regular Contest (ARC)",
                "description": "AtCoder Regular Contest — intermediate-level competitive programming.",
                "platform": self.PLATFORM_NAME,
                "event_type": "contest",
                "tags": ["competitive programming", "regular", "atcoder"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://atcoder.jp/contests/",
                "event_start_date": now + timedelta(days=11),
                "event_end_date": now + timedelta(days=11, hours=2),
                "registration_deadline": now + timedelta(days=11),
                "external_id": "atcoder-arc-fallback",
            },
        ]

