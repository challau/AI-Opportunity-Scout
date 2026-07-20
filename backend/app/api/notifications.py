"""Notifications API."""

import uuid
import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.other import Notification
from app.models.user import User
from app.schemas.schemas import NotificationResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Platforms grouped for the test digest
HACKATHON_PLATFORMS = ["unstop", "devfolio", "hackerearth", "hack2skill", "devpost"]
CP_PLATFORMS = ["codeforces", "codechef", "leetcode", "atcoder"]

MOCK_HACKATHONS = [
    {"title": "AI Innovation Challenge 2026", "platform": "unstop", "registration_deadline": "2026-08-05", "prize": "₹5,00,000", "registration_url": "https://unstop.com/hackathons"},
    {"title": "ETHIndia Hacker House", "platform": "devfolio", "registration_deadline": "2026-08-12", "prize": "$25,000", "registration_url": "https://devfolio.co/hackathons"},
    {"title": "HackerEarth Deep Learning Sprint", "platform": "hackerearth", "registration_deadline": "2026-08-01", "prize": "$10,000", "registration_url": "https://www.hackerearth.com/challenges/"},
    {"title": "Google Cloud Agentic AI Hackathon", "platform": "hack2skill", "registration_deadline": "2026-08-20", "prize": "$15,000", "registration_url": "https://hack2skill.com/"},
    {"title": "Devpost Global AI Buildathon", "platform": "devpost", "registration_deadline": "2026-08-15", "prize": "$20,000", "registration_url": "https://devpost.com/hackathons"},
]

MOCK_CONTESTS = [
    {"title": "Codeforces Round #964 (Div. 2)", "platform": "codeforces", "event_start_date": "2026-07-22 20:05 IST", "duration": "2h", "registration_url": "https://codeforces.com/contests"},
    {"title": "CodeChef Starters 145", "platform": "codechef", "event_start_date": "2026-07-23 20:00 IST", "duration": "2h", "registration_url": "https://www.codechef.com/contests"},
    {"title": "LeetCode Weekly Contest 460", "platform": "leetcode", "event_start_date": "2026-07-26 08:00 IST", "duration": "1h30m", "registration_url": "https://leetcode.com/contest/"},
    {"title": "AtCoder Beginner Contest 415", "platform": "atcoder", "event_start_date": "2026-07-25 17:30 IST", "duration": "1h40m", "registration_url": "https://atcoder.jp/contests/"},
]


async def _collect_test_events(db: AsyncSession) -> tuple[list[dict], list[dict]]:
    """Fetch latest stored events per platform group; fall back to mocks."""
    from app.models.event import Event

    def to_dict(e: Event) -> dict:
        return {
            "title": e.title,
            "platform": e.platform,
            "registration_deadline": str(e.registration_deadline or "Check website"),
            "event_start_date": str(e.event_start_date or "Check website"),
            "prize": e.prize or "Not specified",
            "duration": "See contest page",
            "registration_url": e.registration_url,
        }

    hackathons: list[dict] = []
    contests: list[dict] = []
    try:
        result = await db.execute(
            select(Event)
            .where(and_(Event.is_active == True, Event.platform.in_(HACKATHON_PLATFORMS)))
            .order_by(Event.created_at.desc())
            .limit(5)
        )
        hackathons = [to_dict(e) for e in result.scalars().all()]

        result = await db.execute(
            select(Event)
            .where(and_(Event.is_active == True, Event.platform.in_(CP_PLATFORMS)))
            .order_by(Event.created_at.desc())
            .limit(4)
        )
        contests = [to_dict(e) for e in result.scalars().all()]
    except Exception as e:
        logger.warning("Could not load stored events for test email, using mocks", error=str(e))

    return hackathons or MOCK_HACKATHONS, contests or MOCK_CONTESTS


def _build_test_email(hackathons: list[dict], contests: list[dict]) -> tuple[str, str]:
    """Return (text, html) bodies for the test digest."""
    lines = ["Hello Uday,", "", "Here are your latest opportunities:", "", "=" * 20, "", "🔥 Hackathons", ""]
    for i, h in enumerate(hackathons, 1):
        lines += [
            f"{i}.",
            f"Title: {h['title']}",
            f"Platform: {h['platform'].capitalize()}",
            f"Deadline: {h.get('registration_deadline', 'Check website')}",
            f"Prize: {h.get('prize', 'Not specified')}",
            f"Registration Link: {h['registration_url']}",
            "",
        ]
    lines += ["=" * 20, "", "⚔ Competitive Programming Contests", ""]
    for i, c in enumerate(contests, 1):
        lines += [
            f"{i}.",
            f"Contest Name: {c['title']}",
            f"Platform: {c['platform'].capitalize()}",
            f"Start Time: {c.get('event_start_date', 'Check website')}",
            f"Duration: {c.get('duration', 'See contest page')}",
            f"Contest Link: {c['registration_url']}",
            "",
        ]
    lines += ["=" * 20]
    text = "\n".join(lines)

    def card(rows: list[tuple[str, str]], title: str, url: str) -> str:
        detail = "".join(
            f'<tr><td style="padding:6px 0;color:#94a3b8;font-size:14px;">{k}</td>'
            f'<td style="padding:6px 0;color:#e2e8f0;font-size:14px;text-align:right;">{v}</td></tr>'
            for k, v in rows
        )
        return (
            f'<div style="background:#252540;border:1px solid #3a3a5c;border-radius:12px;padding:20px;margin:14px 0;">'
            f'<div style="font-size:17px;font-weight:700;color:#a78bfa;margin-bottom:10px;">{title}</div>'
            f'<table style="width:100%;border-collapse:collapse;">{detail}</table>'
            f'<a href="{url}" style="display:inline-block;margin-top:12px;padding:8px 18px;background:#6366f1;'
            f'color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">Open →</a></div>'
        )

    hack_cards = "".join(
        card(
            [("Platform", h["platform"].capitalize()),
             ("Deadline", h.get("registration_deadline", "Check website")),
             ("Prize", h.get("prize", "Not specified"))],
            f"{i}. {h['title']}", h["registration_url"],
        )
        for i, h in enumerate(hackathons, 1)
    )
    contest_cards = "".join(
        card(
            [("Platform", c["platform"].capitalize()),
             ("Start Time", c.get("event_start_date", "Check website")),
             ("Duration", c.get("duration", "See contest page"))],
            f"{i}. {c['title']}", c["registration_url"],
        )
        for i, c in enumerate(contests, 1)
    )

    html = f"""
<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px 16px 0 0;padding:36px 30px;text-align:center;">
    <h1 style="color:#fff;font-size:24px;margin:0;">🚀 AI Opportunity Scout</h1>
    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;">Test Notification</p>
  </div>
  <div style="background:#1a1a2e;padding:26px;">
    <p style="color:#e2e8f0;">Hello Uday,</p>
    <p style="color:#94a3b8;">Here are your latest opportunities:</p>
    <h2 style="color:#f59e0b;font-size:18px;margin:22px 0 6px;">🔥 Hackathons</h2>
    {hack_cards}
    <h2 style="color:#38bdf8;font-size:18px;margin:26px 0 6px;">⚔ Competitive Programming Contests</h2>
    {contest_cards}
  </div>
  <div style="background:#0f0f1a;padding:18px;text-align:center;color:#64748b;font-size:12px;border-radius:0 0 16px 16px;">
    AI Opportunity Scout · one-time test notification
  </div>
</div>
</body></html>
"""
    return text, html


@router.get("/test-email")
async def send_test_email(db: AsyncSession = Depends(get_db)):
    """One-time test: email the latest opportunities digest to NOTIFICATION_EMAIL."""
    from app.core.config import settings
    from app.services.email_service import EmailService

    recipient = settings.NOTIFICATION_EMAIL or "challaudaykumar1@gmail.com"

    missing = [
        name for name, value in [
            ("SMTP_HOST", settings.SMTP_HOST),
            ("SMTP_PORT", settings.SMTP_PORT),
            ("SMTP_USERNAME", settings.SMTP_USERNAME),
            ("SMTP_PASSWORD", settings.SMTP_PASSWORD),
        ] if not value
    ]
    if settings.SMTP_USERNAME in ("", "your@gmail.com") or "your-" in settings.SMTP_PASSWORD:
        missing = missing or ["SMTP_USERNAME", "SMTP_PASSWORD"]
    if settings.BREVO_API_KEY:
        missing = []  # HTTPS API path doesn't need SMTP vars
    if missing:
        logger.error("Test email aborted: SMTP not configured", missing=missing)
        return {
            "status": "error",
            "message": "SMTP is not configured — set these environment variables and redeploy.",
            "missing_env_vars": missing,
        }

    logger.info("Email sending started", recipient=recipient)
    hackathons, contests = await _collect_test_events(db)
    text, html = _build_test_email(hackathons, contests)

    logger.info(
        "Connecting to SMTP",
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
    )
    sent = await EmailService().send_email(
        to_email=recipient,
        subject="🚀 AI Opportunity Scout - Test Notification",
        html_content=html,
        text_content=text,
    )
    if sent:
        logger.info("Email sent successfully", recipient=recipient)
        return {
            "status": "success",
            "message": f"Test email sent to {recipient}",
            "hackathons": len(hackathons),
            "contests": len(contests),
            "used_mock_data": hackathons == MOCK_HACKATHONS or contests == MOCK_CONTESTS,
        }
    return {
        "status": "error",
        "message": "SMTP delivery failed after retries — check SMTP credentials and server logs.",
        "recipient": recipient,
    }


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's notifications."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    from fastapi import HTTPException
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == current_user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    return {"message": "Marked as read"}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    from sqlalchemy import update
    await db.execute(
        update(Notification)
        .where(and_(Notification.user_id == current_user.id, Notification.is_read == False))
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    )
    return {"count": result.scalar_one()}
