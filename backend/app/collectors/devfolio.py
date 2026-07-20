"""Devfolio crawler — hackathons."""

from typing import Dict, List

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class DevfolioCrawler(BaseCrawler):
    PLATFORM_NAME = "devfolio"
    API_URL = "https://api.devfolio.co/api/hackathons"

    async def _fetch_events(self) -> List[Dict]:
        params = {"filter": "upcoming", "per_page": 50}
        try:
            data = await self._get_json(self.API_URL, params)
            hackathons = data if isinstance(data, list) else data.get("results", [])
            return [self._parse(h) for h in hackathons if h]
        except Exception as e:
            logger.error("Devfolio crawl failed", error=str(e))
            return []

    def _parse(self, h: Dict) -> Dict:
        return {
            "title": h.get("name", ""),
            "description": h.get("description", ""),
            "platform": self.PLATFORM_NAME,
            "event_type": "hackathon",
            "registration_deadline": h.get("submission_deadline"),
            "event_start_date": h.get("starts_at"),
            "event_end_date": h.get("ends_at"),
            "registration_url": f"https://devfolio.co/hackathons/{h.get('slug', '')}",
            "image_url": h.get("cover_image_url"),
            "organizer": h.get("team_name"),
            "is_remote": h.get("is_online", True),
            "is_free": True,
            "prize": h.get("prize_pool", ""),
            "tags": h.get("themes", []),
            "external_id": str(h.get("id", "")),
            "participant_count": h.get("registered_count", 0),
        }
