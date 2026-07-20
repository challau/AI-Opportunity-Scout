"""Event model — core entity for opportunities."""

import uuid
from datetime import datetime, timezone
from typing import List

from pgvector.sqlalchemy import Vector  # type: ignore
from sqlalchemy import (
    Boolean, DateTime, Float, Index, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        # Composite index for common listing queries: active events sorted by score per platform
        Index("ix_events_platform_active_score", "platform", "is_active", "ai_score"),
        # Index for event type filtering with active flag
        Index("ix_events_type_active", "event_type", "is_active"),
        # Index for deadline-based queries (reminders, upcoming events)
        Index("ix_events_active_deadline", "is_active", "registration_deadline"),
        # Index for deduplication hash lookups
        Index("ix_events_content_hash_unique", "content_hash", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ─── Core Fields ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    short_summary: Mapped[str] = mapped_column(Text, nullable=True)  # AI-generated

    # ─── Classification ───────────────────────────────────────────────────────
    platform: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Types: hackathon|contest|internship|workshop|competition|quiz|open_source|hiring|conference

    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    domains: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    programming_languages: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # ─── Details ──────────────────────────────────────────────────────────────
    prize: Mapped[str] = mapped_column(String(500), nullable=True)
    prize_amount: Mapped[float] = mapped_column(Float, nullable=True)  # Normalized USD
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    eligibility: Mapped[str] = mapped_column(Text, nullable=True)
    organizer: Mapped[str] = mapped_column(String(255), nullable=True)

    # ─── Dates ────────────────────────────────────────────────────────────────
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    event_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    event_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # ─── Links ────────────────────────────────────────────────────────────────
    registration_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=True)

    # ─── AI Fields ────────────────────────────────────────────────────────────
    ai_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 ranking score
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536), nullable=True)

    # ─── Deduplication ────────────────────────────────────────────────────────
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Platform-specific ID

    # ─── Status ───────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    participant_count: Mapped[int] = mapped_column(Integer, default=0)

    # ─── Extra Data ───────────────────────────────────────────────────────────
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    saved_by = relationship("SavedEvent", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event {self.title[:50]} [{self.platform}]>"
