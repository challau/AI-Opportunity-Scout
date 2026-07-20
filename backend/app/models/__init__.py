"""Models package — import all models so Alembic can detect them."""

from app.models.user import User
from app.models.profile import UserProfile
from app.models.event import Event
from app.models.other import SavedEvent, Notification, Resume, CrawlerLog, SchedulerLog

__all__ = [
    "User",
    "UserProfile",
    "Event",
    "SavedEvent",
    "Notification",
    "Resume",
    "CrawlerLog",
    "SchedulerLog",
]
