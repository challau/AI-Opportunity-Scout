"""GSoC, GSSoC, Google, Microsoft, IEEE crawlers."""

from typing import Dict, List

import structlog

from app.collectors.base import BaseCrawler

logger = structlog.get_logger()


class GSoCCrawler(BaseCrawler):
    """Google Summer of Code crawler."""
    PLATFORM_NAME = "gsoc"
    API_URL = "https://summerofcode.withgoogle.com/programs"

    async def _fetch_events(self) -> List[Dict]:
        """GSoC program information (static + scraped)."""
        return [
            {
                "title": "Google Summer of Code 2025",
                "description": "Google Summer of Code is a global program focused on bringing more student developers into open source software development. Students work with an open source organization on a 3 month programming project during their break from school.",
                "platform": self.PLATFORM_NAME,
                "event_type": "open_source",
                "registration_url": "https://summerofcode.withgoogle.com/",
                "organizer": "Google",
                "prize": "$1,500 - $6,600 USD stipend",
                "prize_amount": 6600,
                "is_remote": True,
                "is_free": True,
                "tags": ["gsoc", "google", "open source", "internship", "stipend"],
                "domains": ["Open Source", "Software Engineering"],
            }
        ]


class GSSoCCrawler(BaseCrawler):
    """GirlScript Summer of Code crawler."""
    PLATFORM_NAME = "gssoc"

    async def _fetch_events(self) -> List[Dict]:
        return [
            {
                "title": "GirlScript Summer of Code 2025",
                "description": "GirlScript Summer of Code is a 3-month long open-source program by GirlScript Foundation. Participants contribute to open-source projects under mentors.",
                "platform": self.PLATFORM_NAME,
                "event_type": "open_source",
                "registration_url": "https://gssoc.girlscript.tech/",
                "organizer": "GirlScript Foundation",
                "is_remote": True,
                "is_free": True,
                "tags": ["gssoc", "open source", "student", "india"],
                "domains": ["Open Source", "Software Engineering"],
            }
        ]


class GoogleEventsCrawler(BaseCrawler):
    """Google Developer events (I/O, DSC, GDSC etc.)."""
    PLATFORM_NAME = "google"

    async def _fetch_events(self) -> List[Dict]:
        return [
            {
                "title": "Google Developer Student Clubs Lead Program",
                "description": "GDSC brings Google developer tools and technologies to university students with hands-on projects.",
                "platform": self.PLATFORM_NAME,
                "event_type": "workshop",
                "registration_url": "https://developers.google.com/community/gdsc",
                "organizer": "Google",
                "is_remote": True,
                "is_free": True,
                "tags": ["google", "gdsc", "student", "community"],
                "domains": ["Software Engineering", "Cloud"],
            },
            {
                "title": "Google Solution Challenge 2025",
                "description": "GDSC Solution Challenge is a global competition for GDSC members to create innovative solutions using Google tech.",
                "platform": self.PLATFORM_NAME,
                "event_type": "competition",
                "registration_url": "https://developers.google.com/community/gdsc/solution-challenge",
                "organizer": "Google",
                "prize": "$3,000 USD + Google Mentorship",
                "prize_amount": 3000,
                "is_remote": True,
                "is_free": True,
                "tags": ["google", "competition", "sustainability", "sdg"],
                "domains": ["Software Engineering", "AI/ML"],
            },
        ]


class MicrosoftEventsCrawler(BaseCrawler):
    """Microsoft imagine/learn/certifications events."""
    PLATFORM_NAME = "microsoft"

    async def _fetch_events(self) -> List[Dict]:
        return [
            {
                "title": "Microsoft Imagine Cup 2025",
                "description": "Imagine Cup is Microsoft's global student technology competition. Build a solution that will make a difference.",
                "platform": self.PLATFORM_NAME,
                "event_type": "competition",
                "registration_url": "https://imaginecup.microsoft.com/",
                "organizer": "Microsoft",
                "prize": "$100,000 USD",
                "prize_amount": 100000,
                "is_remote": True,
                "is_free": True,
                "tags": ["microsoft", "competition", "student", "ai", "azure"],
                "domains": ["AI/ML", "Cloud", "Software Engineering"],
            },
            {
                "title": "Microsoft Learn Student Ambassadors Program",
                "description": "Join the Microsoft Learn Student Ambassadors program to build your skills and lead your tech community.",
                "platform": self.PLATFORM_NAME,
                "event_type": "open_source",
                "registration_url": "https://studentambassadors.microsoft.com/",
                "organizer": "Microsoft",
                "is_remote": True,
                "is_free": True,
                "tags": ["microsoft", "student", "community", "ambassador"],
                "domains": ["Cloud", "Software Engineering"],
            },
        ]


class IEEECrawler(BaseCrawler):
    """IEEE events and competitions."""
    PLATFORM_NAME = "ieee"

    async def _fetch_events(self) -> List[Dict]:
        try:
            from bs4 import BeautifulSoup  # type: ignore
            url = "https://www.ieee.org/education/students/student-competitions.html"
            resp = await self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")

            events = []
            # Parse IEEE competition listings
            for link in soup.find_all("a", href=True)[:20]:
                text = link.get_text(strip=True)
                if len(text) > 20 and "competition" in text.lower() or "contest" in text.lower():
                    events.append({
                        "title": text,
                        "description": "IEEE Student Competition",
                        "platform": self.PLATFORM_NAME,
                        "event_type": "competition",
                        "registration_url": link["href"] if link["href"].startswith("http") else f"https://ieee.org{link['href']}",
                        "organizer": "IEEE",
                        "is_remote": False,
                        "is_free": True,
                        "tags": ["ieee", "engineering", "student", "competition"],
                        "domains": ["Engineering", "Electronics"],
                    })
            return events[:10]
        except Exception as e:
            logger.error("IEEE crawl failed", error=str(e))
            return []
