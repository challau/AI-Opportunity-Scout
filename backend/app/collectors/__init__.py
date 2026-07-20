"""Crawler registry — maps platform names to crawler classes."""

from app.collectors.unstop import UnstopCrawler
from app.collectors.devfolio import DevfolioCrawler
from app.collectors.hackerearth import HackerEarthCrawler, HackSkillCrawler
from app.collectors.devpost import DevpostCrawler, KaggleCrawler, MLHCrawler, GitHubEventsCrawler
from app.collectors.codeforces import CodeforcesCrawler, CodeChefCrawler, AtCoderCrawler
from app.collectors.google import GSoCCrawler, GSSoCCrawler, GoogleEventsCrawler, MicrosoftEventsCrawler, IEEECrawler

CRAWLER_REGISTRY = {
    "unstop": UnstopCrawler,
    "devfolio": DevfolioCrawler,
    "hackerearth": HackerEarthCrawler,
    "hack2skill": HackSkillCrawler,
    "devpost": DevpostCrawler,
    "kaggle": KaggleCrawler,
    "mlh": MLHCrawler,
    "github": GitHubEventsCrawler,
    "codeforces": CodeforcesCrawler,
    "codechef": CodeChefCrawler,
    "atcoder": AtCoderCrawler,
    "gsoc": GSoCCrawler,
    "gssoc": GSSoCCrawler,
    "google": GoogleEventsCrawler,
    "microsoft": MicrosoftEventsCrawler,
    "ieee": IEEECrawler,
}


def get_crawler(platform: str):
    """Get crawler instance by platform name."""
    crawler_class = CRAWLER_REGISTRY.get(platform.lower())
    if not crawler_class:
        raise ValueError(f"No crawler found for platform: {platform}")
    return crawler_class()  # type: ignore


def get_all_crawlers():
    """Get instances of all registered crawlers."""
    return [cls() for cls in CRAWLER_REGISTRY.values()]  # type: ignore
