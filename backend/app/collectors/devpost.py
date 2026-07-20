"""Devpost, Kaggle, MLH, GitHub Events crawlers."""

from typing import Dict, List

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class DevpostCrawler(BaseCrawler):
    PLATFORM_NAME = "devpost"
    API_URL = "https://devpost.com/api/hackathons"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL, {"status": "upcoming,open", "per_page": 50})
            hackathons = data.get("hackathons", [])
            return [self._parse(h) for h in hackathons]
        except Exception as e:
            logger.error("Devpost crawl failed", error=str(e))
            return []

    def _parse(self, h: Dict) -> Dict:
        prizes = h.get("prize_amount", "") or ""
        return {
            "title": h.get("title", ""),
            "description": h.get("tagline", ""),
            "platform": self.PLATFORM_NAME,
            "event_type": "hackathon",
            "registration_deadline": h.get("submission_period_dates", "").split(" - ")[-1] if h.get("submission_period_dates") else None,
            "registration_url": h.get("url", ""),
            "image_url": h.get("thumbnail_url"),
            "prize": prizes,
            "is_remote": "online" in h.get("location", "").lower() or not h.get("location"),
            "is_free": True,
            "tags": [t.get("value") for t in h.get("themes", []) if t.get("value")],
            "external_id": str(h.get("id", "")),
            "participant_count": h.get("registrations_count", 0),
        }


class KaggleCrawler(BaseCrawler):
    """Kaggle competitions crawler using public API."""
    PLATFORM_NAME = "kaggle"
    API_URL = "https://www.kaggle.com/api/v1/competitions/list"

    async def _fetch_events(self) -> List[Dict]:
        try:
            data = await self._get_json(self.API_URL, {"sortBy": "recentlyCreated", "pageSize": 30})
            comps: list = data if isinstance(data, list) else []
            return [self._parse(c) for c in comps]
        except Exception as e:
            logger.error("Kaggle crawl failed", error=str(e))
            return []

    def _parse(self, c: Dict) -> Dict:
        return {
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "platform": self.PLATFORM_NAME,
            "event_type": "competition",
            "registration_deadline": c.get("deadline"),
            "registration_url": f"https://kaggle.com/c/{c.get('ref', c.get('id', ''))}",
            "image_url": c.get("imageUrl"),
            "prize": f"${c.get('rewardQuantity', 0):,}" if c.get("rewardQuantity") else "Knowledge",
            "prize_amount": c.get("rewardQuantity"),
            "is_remote": True,
            "is_free": True,
            "tags": ["machine learning", "data science", "AI"],
            "domains": ["AI/ML", "Data Science"],
            "external_id": str(c.get("id", "")),
        }


class MLHCrawler(BaseCrawler):
    """Major League Hacking crawler."""
    PLATFORM_NAME = "mlh"
    URL = "https://mlh.io/seasons/2025/events"

    async def _fetch_events(self) -> List[Dict]:
        try:
            from bs4 import BeautifulSoup  # type: ignore
            resp = await self._get(self.URL)
            soup = BeautifulSoup(resp.text, "lxml")
            events = []
            for event_div in soup.find_all("div", class_="event")[:30]:
                try:
                    title_tag = event_div.find("h3", class_="event-name")
                    date_tag = event_div.find("p", class_="event-date")
                    link_tag = event_div.find("a", class_="event-link")
                    location_tag = event_div.find("div", class_="event-location")

                    if not title_tag:
                        continue

                    events.append({
                        "title": title_tag.get_text(strip=True),
                        "description": "MLH Season Hackathon",
                        "platform": self.PLATFORM_NAME,
                        "event_type": "hackathon",
                        "registration_deadline": date_tag.get_text(strip=True) if date_tag else None,
                        "registration_url": link_tag.get("href", self.URL) if link_tag else self.URL,
                        "location": location_tag.get_text(strip=True) if location_tag else None,
                        "is_remote": False,
                        "is_free": True,
                        "tags": ["mlh", "hackathon", "student"],
                    })
                except Exception:
                    continue
            return events
        except Exception as e:
            logger.error("MLH crawl failed", error=str(e))
            return []


class GitHubEventsCrawler(BaseCrawler):
    """GitHub Campus Events and GitHub Events crawler."""
    PLATFORM_NAME = "github"
    API_URL = "https://api.github.com/events"

    async def _fetch_events(self) -> List[Dict]:
        """Fetch GitHub public events — mostly hackathons and open source programs."""
        # GitHub doesn't have a public events listing API, so we scrape known programs
        events = [
            {
                "title": "GitHub Campus Experts Program",
                "description": "Apply to become a GitHub Campus Expert and lead your student community with GitHub tools and training.",
                "platform": self.PLATFORM_NAME,
                "event_type": "open_source",
                "registration_url": "https://education.github.com/experts",
                "is_remote": True,
                "is_free": True,
                "tags": ["github", "campus", "open source", "community"],
                "domains": ["Open Source", "Community"],
                "organizer": "GitHub Education",
            },
            {
                "title": "GitHub Octernships",
                "description": "Get real-world experience as a student developer through GitHub's internship program with tech companies.",
                "platform": self.PLATFORM_NAME,
                "event_type": "internship",
                "registration_url": "https://github.blog/2022-05-24-github-octernships-real-world-experience-for-students/",
                "is_remote": True,
                "is_free": True,
                "tags": ["github", "internship", "student", "open source"],
                "domains": ["Software Engineering"],
                "organizer": "GitHub",
            },
        ]
        return events
