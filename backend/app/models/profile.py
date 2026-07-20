"""User Profile model with preferences."""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
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

    # Notification settings
    email_notifications: Mapped[bool] = mapped_column(default=True)
    telegram_notifications: Mapped[bool] = mapped_column(default=False)
    notification_frequency: Mapped[str] = mapped_column(String(20), default="daily")  # instant|daily|weekly
    telegram_chat_id: Mapped[str] = mapped_column(String(100), nullable=True)

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
