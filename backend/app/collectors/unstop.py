"""Unstop.com crawler — hackathons, internships, competitions."""

from typing import Dict, List

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class UnstopCrawler(BaseCrawler):
    PLATFORM_NAME = "unstop"
    BASE_URL = "https://unstop.com"
    API_URL = "https://unstop.com/api/public/opportunity/search-new"

    async def _fetch_events(self) -> List[Dict]:
        """Fetch hackathons and competitions from Unstop API."""
        events = []

        opportunity_types = [
            ("hackathon", 1),
            ("competition", 2),
            ("internship", 9),
            ("quiz", 5),
        ]

        for event_type, type_id in opportunity_types:
            try:
                params = {
                    "type": type_id,
                    "page": 1,
                    "size": 50,
                    "sort": "deadline",
                }
                data = await self._get_json(self.API_URL, params)
                raw_items = data.get("data", {}).get("data", [])

                for item in raw_items:
                    event = self._parse_item(item, event_type)
                    if event:
                        events.append(event)

            except Exception as e:
                logger.warning("Unstop type fetch failed", type=event_type, error=str(e))

        logger.info("Unstop crawl", events=len(events))
        return events

    def _parse_item(self, item: Dict, event_type: str) -> Dict:
        """Parse a single Unstop opportunity item."""
        try:
            return {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "platform": self.PLATFORM_NAME,
                "event_type": event_type,
                "prize": item.get("prize", ""),
                "registration_deadline": item.get("end_at"),
                "event_start_date": item.get("start_at"),
                "registration_url": f"{self.BASE_URL}/o/{item.get('seo_url', item.get('id', ''))}",
                "image_url": item.get("banner_image"),
                "organizer": item.get("organisation", {}).get("name"),
                "is_free": item.get("fees_amount", 0) == 0,
                "is_remote": not item.get("is_physical", False),
                "tags": [t.get("name", "") for t in item.get("tags", [])],
                "external_id": str(item.get("id", "")),
                "participant_count": item.get("registrations_count", 0),
            }
        except Exception as e:
            logger.warning("Failed to parse Unstop item", error=str(e))
            return {}
