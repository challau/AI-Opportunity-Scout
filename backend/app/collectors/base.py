"""Base crawler class with common utilities."""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import httpx
import structlog
from fake_useragent import UserAgent  # type: ignore
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()
ua = UserAgent()


class BaseCrawler(ABC):
    """Abstract base class for all platform crawlers."""

    PLATFORM_NAME: str = "unknown"
    BASE_URL: str = ""

    def __init__(self):
        self.timeout = settings.CRAWL_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.delay = settings.RATE_LIMIT_DELAY

    async def crawl(self) -> List[Dict]:
        """
        Main entry point. Returns list of normalized event dicts.
        Subclasses implement _fetch_events().
        """
        logger.info("Crawl started", platform=self.PLATFORM_NAME)
        events = await self._fetch_events()
        logger.info("Crawl complete", platform=self.PLATFORM_NAME, count=len(events))
        return events

    @abstractmethod
    async def _fetch_events(self) -> List[Dict]:
        """Fetch and return raw events from the platform."""
        ...

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": ua.random,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _get(self, url: str, params: Optional[Dict] = None) -> httpx.Response:
        """GET request with retry logic."""
        async with httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            await asyncio.sleep(random.uniform(0.5, self.delay))
            return await client.get(url, params=params)

    async def _get_json(self, url: str, params: Optional[Dict] = None) -> Dict:
        """GET request returning JSON."""
        resp = await self._get(url, params)
        resp.raise_for_status()
        return resp.json()

    def _normalize_event(self, raw: Dict) -> Dict:
        """Override in subclasses to normalize platform-specific data."""
        return {**raw, "platform": self.PLATFORM_NAME}
