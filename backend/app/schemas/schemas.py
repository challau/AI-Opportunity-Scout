"""Pydantic schemas for API request/response validation."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores and hyphens allowed)")
        return v.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str


class UserResponse(UserBase):
    id: uuid.UUID
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    country: Optional[str] = None
    college: Optional[str] = None
    student_year: Optional[int] = Field(None, ge=1, le=6)
    interested_domains: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    preferred_platforms: Optional[List[str]] = None
    selected_sources: Optional[List[str]] = None
    email_notifications: Optional[bool] = None
    notification_enabled: Optional[bool] = None
    telegram_notifications: Optional[bool] = None
    notification_frequency: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    bio: Optional[str] = None
    country: Optional[str] = None
    college: Optional[str] = None
    student_year: Optional[int] = None
    interested_domains: List[str] = []
    programming_languages: List[str] = []
    preferred_platforms: List[str] = []
    selected_sources: List[str] = [
        "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
        "codeforces", "codechef", "leetcode", "atcoder",
    ]
    email_notifications: bool = True
    notification_enabled: bool = True
    telegram_notifications: bool = False
    notification_frequency: str = "hourly"
    telegram_chat_id: Optional[str] = None
    last_notification_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Event Schemas ────────────────────────────────────────────────────────────

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    platform: str
    event_type: str
    tags: List[str] = []
    domains: List[str] = []
    prize: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    is_free: bool = True
    eligibility: Optional[str] = None
    organizer: Optional[str] = None
    registration_deadline: Optional[datetime] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    registration_url: str
    image_url: Optional[str] = None


class EventResponse(EventBase):
    id: uuid.UUID
    short_summary: Optional[str] = None
    ai_score: float = 0.0
    participant_count: int = 0
    is_active: bool = True
    created_at: datetime
    is_saved: Optional[bool] = None  # Set when user is authenticated

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EventFilter(BaseModel):
    platform: Optional[List[str]] = None
    event_type: Optional[List[str]] = None
    domains: Optional[List[str]] = None
    is_remote: Optional[bool] = None
    is_free: Optional[bool] = None
    deadline_before: Optional[datetime] = None
    deadline_after: Optional[datetime] = None
    min_score: Optional[float] = None


# ─── Notification Schemas ─────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: Optional[str] = None
    type: str
    channel: str
    is_read: bool
    event_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Search Schemas ───────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    search_type: str = "hybrid"  # keyword|semantic|hybrid|ai
    filters: Optional[EventFilter] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[EventResponse]
    total: int
    ai_explanation: Optional[str] = None


# ─── AI/Chatbot Schemas ───────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user|assistant
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    message: str
    suggested_events: List[EventResponse] = []
    metadata: dict = {}


# ─── Resume Schemas ───────────────────────────────────────────────────────────

class ResumeResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_size: Optional[int] = None
    skills: dict = {}
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeMatchResult(BaseModel):
    event_id: uuid.UUID
    event_title: str
    match_percentage: float
    matching_skills: List[str]
    explanation: str


# ─── Admin Schemas ────────────────────────────────────────────────────────────

class AdminStats(BaseModel):
    total_users: int
    total_events: int
    total_notifications: int
    events_today: int
    active_crawlers: int
    last_crawl_at: Optional[datetime] = None


class CrawlerLogResponse(BaseModel):
    id: uuid.UUID
    platform: str
    status: str
    events_found: int
    events_new: int
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    started_at: datetime

    model_config = {"from_attributes": True}
