"""User Profile model with preferences."""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class UserProfile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )

    # Personal info
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    college: Mapped[str] = mapped_column(String(255), nullable=True)
    student_year: Mapped[int] = mapped_column(Integer, nullable=True)

    # Preferences
    interested_domains: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    programming_languages: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    preferred_platforms: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Selected sources for notifications (hackathon + CP platforms)
    # e.g. ["unstop", "devfolio", "codeforces", "leetcode"]
    selected_sources: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        default=lambda: [
            "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
            "codeforces", "codechef", "leetcode", "atcoder",
        ],
    )

    # Notification settings
    email_notifications: Mapped[bool] = mapped_column(default=True)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_notifications: Mapped[bool] = mapped_column(default=False)
    notification_frequency: Mapped[str] = mapped_column(String(20), default="hourly")  # instant|hourly|daily|weekly
    telegram_chat_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # Track when this user was last notified (used for dedup / rate-limiting)
    last_notification_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="profile")

