"""Unstop.com crawler — hackathons, internships, competitions."""

from typing import Dict, List, Optional

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class UnstopCrawler(BaseCrawler):
    PLATFORM_NAME = "unstop"
    BASE_URL = "https://unstop.com"
    API_URL = "https://unstop.com/api/public/opportunity/search-new"

    async def _fetch_events(self) -> List[Dict]:
        """Fetch open hackathons and competitions from Unstop API."""
        events = []

        for opportunity in ["hackathons", "competitions", "internships"]:
            try:
                params = {
                    "opportunity": opportunity,
                    "page": 1,
                    "per_page": 30,
                    "oppstatus": "open",
                }
                data = await self._get_json(self.API_URL, params)
                raw_items = data.get("data", {}).get("data", [])

                event_type = opportunity.rstrip("s")
                for item in raw_items:
                    event = self._parse_item(item, event_type)
                    if event:
                        events.append(event)

            except Exception as e:
                logger.warning("Unstop type fetch failed", type=opportunity, error=str(e))

        logger.info("Unstop crawl", events=len(events))
        return events

    def _registration_url(self, item: Dict) -> Optional[str]:
        """Build the event URL. seo_url may be a full URL; public_url is a path."""
        seo = item.get("seo_url") or ""
        if seo.startswith("http"):
            return seo
        public = item.get("public_url") or seo
        if public:
            return f"{self.BASE_URL}/{public.lstrip('/')}"
        return None

    @staticmethod
    def _prize_text(item: Dict) -> Optional[str]:
        prizes = item.get("prizes") or []
        cash = [p.get("cash") for p in prizes if p.get("cash")]
        if cash:
            currency = "₹" if "rupee" in str(prizes[0].get("currency", "")) else ""
            return f"{currency}{int(sum(cash)):,}"
        return None

    @staticmethod
    def _image_url(item: Dict) -> Optional[str]:
        """banner_mobile/logoUrl2 may be dicts ({image_url: ...}) or strings."""
        for key in ("banner_mobile", "logoUrl2"):
            val = item.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, dict):
                url = val.get("image_url") or val.get("url")
                if isinstance(url, str) and url:
                    return url
        return None

    def _parse_item(self, item: Dict, event_type: str) -> Dict:
        """Parse a single Unstop opportunity item."""
        try:
            url = self._registration_url(item)
            if not url:
                return {}
            regn = item.get("regnRequirements") or {}
            return {
                "title": item.get("title", ""),
                "description": (item.get("details") or "")[:2000],
                "platform": self.PLATFORM_NAME,
                "event_type": event_type,
                "prize": self._prize_text(item),
                "registration_deadline": regn.get("end_regn_dt") or item.get("end_date"),
                "event_start_date": item.get("start_date"),
                "event_end_date": item.get("end_date"),
                "registration_url": url,
                "image_url": self._image_url(item),
                "organizer": (item.get("organisation") or {}).get("name"),
                "is_free": not item.get("isPaid", False),
                "is_remote": item.get("region") != "offline",
                "tags": [f.get("name", "") for f in (item.get("filters") or []) if f.get("name")][:8],
                "external_id": str(item.get("id", "")),
                "participant_count": item.get("registerCount", 0),
            }
        except Exception as e:
            logger.warning("Failed to parse Unstop item", error=str(e))
            return {}
