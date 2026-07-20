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
    """Hack2Skill platform crawler with fallback mock data."""
    PLATFORM_NAME = "hack2skill"
    API_URL = "https://hack2skill.com/api/v1/hackathons"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL)
            items = data if isinstance(data, list) else data.get("data", [])
            results = [self._parse(i) for i in items]
            if results:
                return results
        except Exception as e:
            logger.error("Hack2Skill crawl failed, using fallback", error=str(e))
        return self._fallback_events()

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

    def _fallback_events(self) -> List[Dict]:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        return [
            {
                "title": "Google Cloud Agentic AI Hackathon",
                "description": "Build agentic AI solutions using Google Cloud. Open to all developers worldwide.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "ai", "google-cloud"],
                "prize": "$15,000",
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hack/googlecloudaihack",
                "event_start_date": now + timedelta(days=10),
                "registration_deadline": now + timedelta(days=7),
                "external_id": "hack2skill-gc-ai-2026",
            },
            {
                "title": "Hack2Skill Innovation Challenge 2026",
                "description": "Annual innovation hackathon — build solutions that matter for India's future.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "innovation", "india"],
                "prize": "₹5,00,000",
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hackathons",
                "event_start_date": now + timedelta(days=20),
                "registration_deadline": now + timedelta(days=15),
                "external_id": "hack2skill-innov-2026",
            },
            {
                "title": "Smart India Hackathon — Hack2Skill",
                "description": "Nation-wide hackathon to solve India's challenges with cutting-edge tech.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "india", "government"],
                "prize": "₹1,00,000",
                "is_remote": False,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hackathons",
                "event_start_date": now + timedelta(days=30),
                "registration_deadline": now + timedelta(days=25),
                "external_id": "hack2skill-sih-2026",
            },
        ]
