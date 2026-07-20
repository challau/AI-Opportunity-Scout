"""HackerEarth crawler."""

from typing import Dict, List
import structlog
from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class HackerEarthCrawler(BaseCrawler):
    PLATFORM_NAME = "hackerearth"
    API_URL = "https://www.hackerearth.com/chrome-extension/events/"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL)
            events = []
            for category in ["upcoming", "ongoing"]:
                for item in data.get(category, []):
                    events.append(self._parse(item, category))
            return events
        except Exception as e:
            logger.error("HackerEarth crawl failed", error=str(e))
            return []

    def _parse(self, item: Dict, status: str) -> Dict:
        return {
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "platform": self.PLATFORM_NAME,
            "event_type": self._map_type(item.get("type", "")),
            "registration_deadline": item.get("end_tz"),
            "event_start_date": item.get("start_tz"),
            "registration_url": item.get("url", ""),
            "image_url": item.get("cover_image"),
            "is_remote": True,
            "is_free": True,
            "prize": item.get("prize_amount", ""),
            "tags": item.get("skills", []),
            "external_id": str(item.get("id", "")),
        }

    def _map_type(self, t: str) -> str:
        mapping = {
            "hackathon": "hackathon",
            "challenge": "contest",
            "hiring_challenge": "hiring",
            "sprint": "contest",
            "marathon": "contest",
        }
        return mapping.get(t.lower(), "contest")


class HackSkillCrawler(BaseCrawler):
    """Hack2Skill platform crawler."""
    PLATFORM_NAME = "hack2skill"
    API_URL = "https://hack2skill.com/api/v1/hackathons"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL)
            items = data if isinstance(data, list) else data.get("data", [])
            return [self._parse(i) for i in items]
        except Exception as e:
            logger.error("Hack2Skill crawl failed", error=str(e))
            return []

    def _parse(self, item: Dict) -> Dict:
        return {
            "title": item.get("name", ""),
            "description": item.get("description", ""),
            "platform": self.PLATFORM_NAME,
            "event_type": "hackathon",
            "registration_deadline": item.get("registration_end_date"),
            "event_start_date": item.get("start_date"),
            "registration_url": item.get("url") or f"https://hack2skill.com/hack/{item.get('slug', '')}",
            "image_url": item.get("banner_url"),
            "prize": item.get("prize_pool", ""),
            "is_remote": item.get("mode", "").lower() in ["online", "virtual"],
            "is_free": item.get("fees", 0) == 0,
            "tags": item.get("tags", []),
            "external_id": str(item.get("id", "")),
        }
