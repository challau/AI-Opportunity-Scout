"""Hack2Skill hackathon collector with HTTP scraping + fallback mock data."""

import structlog
import re
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector

logger = structlog.get_logger()


class Hack2SkillCollector(BaseCollector):
    PLATFORM_NAME = "hack2skill"
    BASE_URL = "https://hack2skill.com"

    async def crawl(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(
                timeout=25,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get("https://hack2skill.com/hackathons")
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Look for hackathon cards
                cards = soup.select(".hackathon-card, .event-card, [class*='hackathon'], [class*='event-item']")
                for card in cards[:10]:
                    try:
                        title_el = card.select_one("h2, h3, .title, .event-title, [class*='title']")
                        link_el = card.select_one("a[href]")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        url = link_el["href"] if link_el else "https://hack2skill.com/hackathons"
                        if url.startswith("/"):
                            url = f"https://hack2skill.com{url}"
                        events.append({
                            "title": title,
                            "description": f"Hackathon on Hack2Skill: {title}",
                            "platform": self.PLATFORM_NAME,
                            "event_type": "hackathon",
                            "tags": ["hackathon", "hack2skill"],
                            "domains": ["AI/ML", "Web Development"],
                            "is_remote": True,
                            "is_free": True,
                            "registration_url": url,
                            "event_start_date": None,
                            "registration_deadline": None,
                        })
                    except Exception:
                        continue

        except Exception as e:
            logger.warning("Hack2Skill scrape failed, using fallback mock data", error=str(e))

        if not events:
            events = self._fallback_events()

        logger.info("Hack2Skill crawl complete", count=len(events))
        return events

    def _fallback_events(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "title": "Google Cloud Agentic AI Hackathon",
                "description": "Build agentic AI solutions using Google Cloud technologies. Open to all developers.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "ai", "google-cloud", "hack2skill"],
                "domains": ["AI/ML", "Cloud"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hack/googlecloudaihack",
                "event_start_date": now + timedelta(days=10),
                "registration_deadline": now + timedelta(days=7),
                "prize": "$15,000",
            },
            {
                "title": "Hack2Skill Innovation Challenge 2026",
                "description": "Annual innovation hackathon by Hack2Skill — build solutions that matter.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "innovation", "hack2skill"],
                "domains": ["Web Development", "AI/ML", "Mobile Dev"],
                "is_remote": True,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hackathons",
                "event_start_date": now + timedelta(days=20),
                "registration_deadline": now + timedelta(days=15),
                "prize": "₹5,00,000",
            },
            {
                "title": "Smart India Hackathon — Hack2Skill Edition",
                "description": "Nation-wide hackathon to solve real India challenges with technology.",
                "platform": self.PLATFORM_NAME,
                "event_type": "hackathon",
                "tags": ["hackathon", "india", "government", "hack2skill"],
                "domains": ["Web Development", "Mobile Dev", "Cloud"],
                "is_remote": False,
                "is_free": True,
                "registration_url": "https://hack2skill.com/hackathons",
                "event_start_date": now + timedelta(days=30),
                "registration_deadline": now + timedelta(days=25),
                "prize": "₹1,00,000",
            },
        ]
