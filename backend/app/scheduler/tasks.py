"""APScheduler background jobs for crawling and notifications with robustness & idempotency."""

import asyncio
import json
from datetime import datetime, timezone
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
import redis.asyncio as aioredis

from sqlalchemy import select
from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.other import SchedulerLog, CrawlerLog, Notification, SavedEvent
from app.models.event import Event
from app.models.user import User
from app.models.profile import UserProfile

logger = structlog.get_logger()

# Helper to get Redis client
def get_redis_client():
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def run_crawl_task(platform: str = "all", trigger_source: str = "scheduled") -> None:
    """Run crawlers and process events through AI pipeline with tenacity retry."""
    from app.collectors import get_all_crawlers, get_crawler
    from app.ai.coordinator import AICoordinator
    from app.repositories.event_repository import EventRepository
    from app.services.embedding_service import EmbeddingService

    start_time = datetime.now(timezone.utc)
    job_id = f"crawl_{platform}"
    job_name = f"Crawl {platform} platforms"
    
    # Initialize scheduler log entry
    scheduler_log = SchedulerLog(
        job_id=job_id,
        job_name=job_name,
        status="running",
        started_at=start_time,
        platforms_crawled=[],
        failures={},
        trigger_source=trigger_source,
    )
    
    async with AsyncSessionLocal() as db:
        db.add(scheduler_log)
        await db.commit()
        await db.refresh(scheduler_log)

    coordinator = AICoordinator()
    embedding_service = EmbeddingService()

    if platform == "all":
        crawlers = get_all_crawlers()
    else:
        try:
            crawlers = [get_crawler(platform)]
        except Exception as e:
            logger.error("Failed to load crawler", platform=platform, error=str(e))
            async with AsyncSessionLocal() as db:
                scheduler_log.status = "failed"
                scheduler_log.completed_at = datetime.now(timezone.utc)
                scheduler_log.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
                scheduler_log.error_message = f"Failed to load crawler: {str(e)}"
                db.add(scheduler_log)
                await db.commit()
            return

    platforms_crawled = [c.PLATFORM_NAME for c in crawlers]
    failures = {}
    events_found = 0
    events_new = 0

    # Define retryable crawl function per platform
    @retry(
        stop=stop_after_attempt(settings.SCHEDULER_MAX_CRAWL_RETRIES),
        wait=wait_exponential(multiplier=2, min=5, max=settings.SCHEDULER_CRAWL_RETRY_DELAY_SECONDS),
        reraise=True
    )
    async def _crawl_platform_with_retry(crawler):
        return await crawler.crawl()

    for crawler in crawlers:
        p_name = crawler.PLATFORM_NAME
        logger.info("Starting crawl for platform", platform=p_name)
        
        async with AsyncSessionLocal() as db:
            crawler_log = CrawlerLog(
                platform=p_name,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            db.add(crawler_log)
            await db.commit()
            await db.refresh(crawler_log)

        p_start_time = datetime.now(timezone.utc)
        
        try:
            # Execute with exponential backoff on failure
            raw_events = await _crawl_platform_with_retry(crawler)
            
            if not raw_events:
                async with AsyncSessionLocal() as db:
                    crawler_log.status = "partial"
                    crawler_log.events_found = 0
                    crawler_log.completed_at = datetime.now(timezone.utc)
                    crawler_log.duration_seconds = (datetime.now(timezone.utc) - p_start_time).total_seconds()
                    db.add(crawler_log)
                    await db.commit()
                continue

            events_found += len(raw_events)

            # Process through AI pipeline
            async with AsyncSessionLocal() as db:
                result = await coordinator.run_pipeline(raw_events, p_name, db)
                processed = result.get("summarized_events", [])

                # Save to database
                repo = EventRepository(db)
                p_new_count = 0

                for event_data in processed:
                    content_hash = event_data.get("content_hash")
                    if not content_hash:
                        continue

                    existing = await repo.get_by_content_hash(content_hash)
                    if existing:
                        continue

                    # Generate embedding
                    event_text = embedding_service.event_to_text(event_data)
                    embedding = await embedding_service.get_embedding(event_text)

                    # Parse deadline
                    deadline = None
                    deadline_raw = event_data.get("deadline") or event_data.get("registration_deadline")
                    if deadline_raw:
                        try:
                            if isinstance(deadline_raw, str):
                                deadline = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))
                            elif isinstance(deadline_raw, datetime):
                                deadline = deadline_raw
                        except (ValueError, TypeError):
                            pass

                    event = Event(
                        title=event_data.get("title", "")[:500],
                        description=event_data.get("description"),
                        short_summary=event_data.get("short_summary"),
                        platform=event_data.get("platform", p_name),
                        event_type=event_data.get("event_type", "hackathon"),
                        tags=event_data.get("tags", []),
                        domains=event_data.get("domains", []),
                        prize=event_data.get("prize"),
                        location=event_data.get("location"),
                        is_remote=event_data.get("is_remote", False),
                        is_free=event_data.get("is_free", True),
                        eligibility=event_data.get("eligibility"),
                        organizer=event_data.get("organizer"),
                        registration_deadline=deadline,
                        registration_url=event_data.get("registration_url", ""),
                        image_url=event_data.get("image_url"),
                        ai_score=event_data.get("ai_score", 50.0),
                        embedding=embedding,
                        content_hash=content_hash,
                        external_id=event_data.get("external_id"),
                        participant_count=event_data.get("participant_count", 0),
                    )
                    db.add(event)
                    p_new_count += 1

                await db.commit()
                events_new += p_new_count

                # Update crawler log
                duration = (datetime.now(timezone.utc) - p_start_time).total_seconds()
                crawler_log.status = "success"
                crawler_log.events_found = len(raw_events)
                crawler_log.events_new = p_new_count
                crawler_log.duration_seconds = duration
                crawler_log.completed_at = datetime.now(timezone.utc)
                db.add(crawler_log)
                await db.commit()

        except Exception as e:
            duration = (datetime.now(timezone.utc) - p_start_time).total_seconds()
            err_msg = str(e)[:1000]
            failures[p_name] = err_msg
            logger.error("Platform crawl task failed after retries", platform=p_name, error=err_msg)
            
            async with AsyncSessionLocal() as db:
                crawler_log.status = "failed"
                crawler_log.error_message = err_msg
                crawler_log.duration_seconds = duration
                crawler_log.completed_at = datetime.now(timezone.utc)
                db.add(crawler_log)
                await db.commit()

    # Trigger notifications if we found new opportunities
    if events_new > 0:
        asyncio.create_task(notify_users_of_new_events())

    # Finalize scheduler log entry
    end_time = datetime.now(timezone.utc)
    duration_total = (end_time - start_time).total_seconds()
    status = "failed" if len(failures) == len(crawlers) and crawlers else "success"
    
    async with AsyncSessionLocal() as db:
        # Load fresh copy of scheduler_log
        scheduler_log = await db.get(SchedulerLog, scheduler_log.id)
        if scheduler_log:
            scheduler_log.status = status
            scheduler_log.completed_at = end_time
            scheduler_log.duration_seconds = duration_total
            scheduler_log.platforms_crawled = platforms_crawled
            scheduler_log.events_found = events_found
            scheduler_log.events_new = events_new
            scheduler_log.failures = failures
            if failures:
                scheduler_log.error_message = f"Failures on: {', '.join(failures.keys())}"
            db.add(scheduler_log)
            await db.commit()

    logger.info("Crawler job execution completed", platform=platform, status=status, new_events=events_new)


async def notify_users_of_new_events() -> int:
    """Send in-app notifications to users about new events matching their interests. Returns count sent."""
    from app.services.recommendation_service import RecommendationService
    
    service = RecommendationService()
    notifications_created = 0
    
    async with AsyncSessionLocal() as db:
        users_result = await db.execute(select(User).where(User.is_active == True))
        users = list(users_result.scalars().all())

        for user in users:
            try:
                events = await service.get_recommendations(user, db, limit=3)
                for event in events:
                    # Idempotency check for in-app notifications
                    notif_exists = await db.execute(
                        select(Notification).where(
                            Notification.user_id == user.id,
                            Notification.event_id == event.id,
                            Notification.type == "new_event"
                        )
                    )
                    if notif_exists.scalar_one_or_none():
                        continue
                        
                    notif = Notification(
                        user_id=user.id,
                        title=f"New: {event.title[:50]}",
                        body=event.short_summary or event.description[:200] if event.description else "",
                        type="new_event",
                        event_id=event.id,
                        channel="in_app",
                    )
                    db.add(notif)
                    notifications_created += 1
                await db.commit()
            except Exception as e:
                logger.warning("User notification mapping failed", user_id=str(user.id), error=str(e))
                
    return notifications_created


async def run_daily_digest(trigger_source: str = "scheduled") -> None:
    """Send daily digest emails and Telegram messages with strict Redis-based idempotency."""
    from app.services.email_service import EmailService
    from app.services.telegram_service import TelegramService
    from app.services.recommendation_service import RecommendationService

    start_time = datetime.now(timezone.utc)
    scheduler_log = SchedulerLog(
        job_id="daily_digest",
        job_name="Send daily digest",
        status="running",
        started_at=start_time,
        trigger_source=trigger_source,
    )
    
    async with AsyncSessionLocal() as db:
        db.add(scheduler_log)
        await db.commit()
        await db.refresh(scheduler_log)

    email_service = EmailService()
    telegram_service = TelegramService()
    rec_service = RecommendationService()

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_display = datetime.now(timezone.utc).strftime("%B %d, %Y")

    emails_sent = 0
    telegrams_sent = 0
    failures = {}

    redis_client = get_redis_client()

    try:
        async with AsyncSessionLocal() as db:
            users_result = await db.execute(select(User).where(User.is_active == True))
            users = list(users_result.scalars().all())

            for user in users:
                profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == user.id)
                )
                profile = profile_result.scalar_one_or_none()

                if not profile:
                    continue

                # Check if notifications are enabled
                wants_email = profile.email_notifications and profile.notification_frequency in ["daily", "instant"]
                wants_telegram = profile.telegram_notifications and bool(profile.telegram_chat_id)

                if not (wants_email or wants_telegram):
                    continue

                events = await rec_service.get_recommendations(user, db, limit=5)
                if not events:
                    continue

                event_dicts = [
                    {
                        "title": e.title, "platform": e.platform,
                        "prize": e.prize, "registration_url": e.registration_url,
                        "registration_deadline": str(e.registration_deadline),
                        "short_summary": e.short_summary,
                    }
                    for e in events
                ]

                # ─── Email digest with Redis idempotency check ────────────────────
                if wants_email:
                    email_lock_key = f"scheduler:digest:email:{user.id}:{today_str}"
                    # Lock for 26 hours to span across daily runs safely
                    if await redis_client.set(email_lock_key, "1", ex=26 * 3600, nx=True):
                        try:
                            sent = await email_service.send_opportunity_notification(
                                user_name=user.full_name,
                                to_email=user.email,
                                event=event_dicts[0],
                                ai_reason="Based on your interests and recent activity.",
                            )
                            if sent:
                                emails_sent += 1
                            else:
                                # Revert lock if sending failed so it can be retried
                                await redis_client.delete(email_lock_key)
                        except Exception as e:
                            await redis_client.delete(email_lock_key)
                            failures[f"email_{user.id}"] = str(e)
                    else:
                        logger.info("Skip duplicate daily email digest", user_id=str(user.id))

                # ─── Telegram digest with Redis idempotency check ─────────────────
                if wants_telegram:
                    tg_lock_key = f"scheduler:digest:tg:{user.id}:{today_str}"
                    if await redis_client.set(tg_lock_key, "1", ex=26 * 3600, nx=True):
                        try:
                            sent = await telegram_service.send_daily_digest(
                                chat_id=profile.telegram_chat_id,
                                events=event_dicts,
                                date_str=today_display,
                            )
                            if sent:
                                telegrams_sent += 1
                            else:
                                await redis_client.delete(tg_lock_key)
                        except Exception as e:
                            await redis_client.delete(tg_lock_key)
                            failures[f"tg_{user.id}"] = str(e)
                    else:
                        logger.info("Skip duplicate daily telegram digest", user_id=str(user.id))

        status = "failed" if failures and (emails_sent == 0 and telegrams_sent == 0) else "success"
    except Exception as outer_err:
        status = "failed"
        failures["system"] = str(outer_err)
        logger.error("Daily digest task failed", error=str(outer_err))
    finally:
        await redis_client.close()

    end_time = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        scheduler_log = await db.get(SchedulerLog, scheduler_log.id)
        if scheduler_log:
            scheduler_log.status = status
            scheduler_log.completed_at = end_time
            scheduler_log.duration_seconds = (end_time - start_time).total_seconds()
            scheduler_log.emails_sent = emails_sent
            scheduler_log.telegrams_sent = telegrams_sent
            scheduler_log.failures = failures
            if failures:
                scheduler_log.error_message = json.dumps(failures)[:1000]
            db.add(scheduler_log)
            await db.commit()


async def run_deadline_reminders(trigger_source: str = "scheduled") -> None:
    """Send reminders for events with upcoming deadlines (3 days) with strict Redis-based idempotency."""
    from app.repositories.event_repository import EventRepository
    from app.services.telegram_service import TelegramService
    from app.models.other import SavedEvent

    start_time = datetime.now(timezone.utc)
    scheduler_log = SchedulerLog(
        job_id="deadline_reminders",
        job_name="Send deadline reminders",
        status="running",
        started_at=start_time,
        trigger_source=trigger_source,
    )
    
    async with AsyncSessionLocal() as db:
        db.add(scheduler_log)
        await db.commit()
        await db.refresh(scheduler_log)

    telegram = TelegramService()
    telegrams_sent = 0
    failures = {}

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    redis_client = get_redis_client()

    try:
        async with AsyncSessionLocal() as db:
            repo = EventRepository(db)
            upcoming = await repo.get_upcoming_deadlines(days=3)

            if upcoming:
                users_result = await db.execute(select(User).where(User.is_active == True))
                users = list(users_result.scalars().all())

                for user in users:
                    profile_result = await db.execute(
                        select(UserProfile).where(UserProfile.user_id == user.id)
                    )
                    profile = profile_result.scalar_one_or_none()
                    
                    if not profile or not profile.telegram_notifications or not profile.telegram_chat_id:
                        continue

                    # Check for saved events with upcoming deadlines
                    saved_result = await db.execute(
                        select(SavedEvent).where(SavedEvent.user_id == user.id)
                    )
                    saved_event_ids = {s.event_id for s in saved_result.scalars().all()}

                    for event in upcoming:
                        if event.id in saved_event_ids and event.registration_deadline:
                            # Strict idempotency lock per user, event, and day
                            reminder_lock_key = f"scheduler:reminder:{user.id}:{event.id}:{today_str}"
                            
                            if await redis_client.set(reminder_lock_key, "1", ex=26 * 3600, nx=True):
                                try:
                                    days_left = (event.registration_deadline - datetime.now(timezone.utc)).days
                                    event_dict = {
                                        "title": event.title,
                                        "registration_url": event.registration_url,
                                    }
                                    sent = await telegram.send_deadline_reminder(
                                        profile.telegram_chat_id, event_dict, max(0, days_left)
                                    )
                                    if sent:
                                        telegrams_sent += 1
                                    else:
                                        await redis_client.delete(reminder_lock_key)
                                except Exception as e:
                                    await redis_client.delete(reminder_lock_key)
                                    failures[f"reminder_{user.id}_{event.id}"] = str(e)
                            else:
                                logger.debug("Skip duplicate deadline reminder", user_id=str(user.id), event_id=str(event.id))

        status = "failed" if failures and telegrams_sent == 0 else "success"
    except Exception as outer_err:
        status = "failed"
        failures["system"] = str(outer_err)
        logger.error("Deadline reminders task failed", error=str(outer_err))
    finally:
        await redis_client.close()

    end_time = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        scheduler_log = await db.get(SchedulerLog, scheduler_log.id)
        if scheduler_log:
            scheduler_log.status = status
            scheduler_log.completed_at = end_time
            scheduler_log.duration_seconds = (end_time - start_time).total_seconds()
            scheduler_log.telegrams_sent = telegrams_sent
            scheduler_log.failures = failures
            if failures:
                scheduler_log.error_message = json.dumps(failures)[:1000]
            db.add(scheduler_log)
            await db.commit()


# ─── Hourly opportunity notifications ─────────────────────────────────────────

HOURLY_PLATFORMS = [
    "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
    "codeforces", "codechef", "leetcode", "atcoder",
]

HACKATHON_SET = {"unstop", "devfolio", "hackerearth", "hack2skill", "devpost"}


def _parse_dt(value):
    """Best-effort conversion of crawler date values to aware datetimes."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        for candidate in (value, value.replace("Z", "+00:00")):
            try:
                return datetime.fromisoformat(candidate)
            except (ValueError, TypeError):
                continue
    return None


def _hourly_personalized_digest_email(user_name: str, recipient: str, matched_events: list) -> tuple[str, str]:
    """Build personalized (text, html) digest for a specific user."""
    from app.core.config import settings
    hackathons = [e for e in matched_events if e.platform in HACKATHON_SET]
    contests = [e for e in matched_events if e.platform not in HACKATHON_SET]

    def fmt(dt):
        return dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "Check website"

    def text_block(events, header):
        if not events:
            return []
        lines = ["=" * 20, "", header, ""]
        for i, e in enumerate(events, 1):
            lines += [
                f"{i}. {e.title}",
                f"   Platform: {e.platform.capitalize()}",
                f"   Start date: {fmt(e.event_start_date)}",
                f"   Deadline: {fmt(e.registration_deadline)}",
                f"   Prize: {e.prize or 'Not specified'}",
                f"   Link: {e.registration_url}",
                "",
            ]
        return lines

    unsubscribe_url = f"{settings.API_URL}/api/users/unsubscribe?email={recipient}"

    text = "\n".join(
        [f"Hello {user_name or 'there'},", "", "New opportunities matching your preferences:", ""]
        + text_block(hackathons, "🔥 New Hackathons")
        + text_block(contests, "⚔ New Coding Contests")
        + ["=" * 20, "", f"Want to stop receiving these? Unsubscribe here: {unsubscribe_url}"]
    )

    def html_cards(events):
        cards = []
        for e in events:
            rows = "".join(
                f'<tr><td style="padding:5px 0;color:#94a3b8;font-size:13px;">{k}</td>'
                f'<td style="padding:5px 0;color:#e2e8f0;font-size:13px;text-align:right;">{v}</td></tr>'
                for k, v in [
                    ("Platform", e.platform.capitalize()),
                    ("Start date", fmt(e.event_start_date)),
                    ("Deadline", fmt(e.registration_deadline)),
                    ("Prize", e.prize or "Not specified"),
                ]
            )
            cards.append(
                f'<div style="background:#252540;border:1px solid #3a3a5c;border-radius:12px;padding:18px;margin:12px 0;">'
                f'<div style="font-size:16px;font-weight:700;color:#a78bfa;margin-bottom:8px;">{e.title}</div>'
                f'<table style="width:100%;border-collapse:collapse;">{rows}</table>'
                f'<a href="{e.registration_url}" style="display:inline-block;margin-top:10px;padding:8px 18px;'
                f'background:#6366f1;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;'
                f'font-size:13px;">Open →</a></div>'
            )
        return "".join(cards)

    sections = ""
    if hackathons:
        sections += f'<h2 style="color:#f59e0b;font-size:17px;margin:20px 0 4px;">🔥 New Hackathons</h2>{html_cards(hackathons)}'
    if contests:
        sections += f'<h2 style="color:#38bdf8;font-size:17px;margin:20px 0 4px;">⚔ New Coding Contests</h2>{html_cards(contests)}'

    html = (
        '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;'
        "font-family:'Segoe UI',Arial,sans-serif;\">"
        '<div style="max-width:600px;margin:0 auto;padding:20px;">'
        '<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px 16px 0 0;'
        'padding:32px 28px;text-align:center;">'
        f'<h1 style="color:#fff;font-size:22px;margin:0;">🚀 AI Opportunity Scout</h1>'
        f'<p style="color:rgba(255,255,255,0.85);margin:6px 0 0;">Personalized opportunities digest</p></div>'
        f'<div style="background:#1a1a2e;padding:24px;">{sections}</div>'
        f'<div style="background:#0f0f1a;padding:16px;text-align:center;color:#64748b;font-size:12px;'
        f'border-radius:0 0 16px 16px;">'
        f'AI Opportunity Scout · hourly scan<br/>'
        f'Want to stop receiving these? <a href="{unsubscribe_url}" style="color:#a78bfa;text-decoration:underline;">Unsubscribe here</a>.</div>'
        '</div></body></html>'
    )
    return text, html


async def run_hourly_notifications(trigger_source: str = "scheduled") -> dict:
    """Crawl target platforms, store deduplicated events, email active users personalized notifications."""
    from app.ai.duplicate_agent import _compute_content_hash
    from app.services.email_service import EmailService

    start_time = datetime.now(timezone.utc)
    logger.info("Hourly notification job started", trigger_source=trigger_source)

    scheduler_log = SchedulerLog(
        job_id="hourly_notifications",
        job_name="Hourly opportunity notifications",
        status="running",
        started_at=start_time,
        platforms_crawled=HOURLY_PLATFORMS,
        trigger_source=trigger_source,
    )
    async with AsyncSessionLocal() as db:
        db.add(scheduler_log)
        await db.commit()
        await db.refresh(scheduler_log)
    log_id = scheduler_log.id

    from app.collectors import get_crawler

    events_found = 0
    duplicates_removed = 0
    failures = {}
    new_event_ids = []

    for platform in HOURLY_PLATFORMS:
        try:
            crawler = get_crawler(platform)
            raw_events = await crawler.crawl()
        except Exception as e:
            failures[platform] = str(e)[:300]
            logger.error("Crawler failed", platform=platform, error=str(e))
            continue

        logger.info("Crawler completed", platform=platform, events=len(raw_events))
        events_found += len(raw_events)

        async with AsyncSessionLocal() as db:
            for raw in raw_events:
                if not raw.get("title") or not raw.get("registration_url"):
                    continue
                content_hash = _compute_content_hash(raw)  # title|platform|registration_url
                exists = await db.execute(
                    select(Event.id).where(Event.content_hash == content_hash).limit(1)
                )
                if exists.scalar_one_or_none():
                    duplicates_removed += 1
                    continue
                event = Event(
                    title=raw.get("title", "")[:500],
                    description=raw.get("description"),
                    platform=raw.get("platform", platform),
                    event_type=raw.get("event_type", "hackathon"),
                    tags=raw.get("tags") or [],
                    domains=raw.get("domains") or [],
                    prize=str(raw["prize"])[:500] if raw.get("prize") else None,
                    location=raw.get("location"),
                    is_remote=raw.get("is_remote", True),
                    is_free=raw.get("is_free", True),
                    eligibility=raw.get("eligibility"),
                    organizer=raw.get("organizer"),
                    registration_deadline=_parse_dt(raw.get("registration_deadline")),
                    event_start_date=_parse_dt(raw.get("event_start_date")),
                    event_end_date=_parse_dt(raw.get("event_end_date")),
                    registration_url=raw.get("registration_url", ""),
                    image_url=raw.get("image_url"),
                    content_hash=content_hash,
                    external_id=str(raw.get("external_id") or "") or None,
                )
                db.add(event)
                await db.flush()
                new_event_ids.append(event.id)
            await db.commit()

    logger.info(
        "New events found",
        new=len(new_event_ids),
        found=events_found,
        duplicates_removed=duplicates_removed,
    )

    emails_sent = 0
    if new_event_ids:
        email_service = EmailService()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Event).where(Event.id.in_(new_event_ids)))
            new_events = list(result.scalars().all())
            # Cap digest size so emails stay readable
            new_events = new_events[:25]

            # 2. Select active users with email notifications enabled and set to hourly
            users_query = select(User).join(UserProfile).where(
                User.is_active == True,
                UserProfile.notification_enabled == True,
                UserProfile.notification_frequency == "hourly"
            )
            users_result = await db.execute(users_query)
            active_users = list(users_result.scalars().all())

            # Also query user profiles explicitly to avoid lazy loading issues
            for user in active_users:
                # Reload profile in session
                profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
                profile = profile_result.scalar_one_or_none()
                if not profile:
                    continue

                selected = profile.selected_sources or []
                matched_events = [e for e in new_events if e.platform.lower() in [s.lower() for s in selected]]

                if not matched_events:
                    continue

                text, html = _hourly_personalized_digest_email(user.full_name, user.email, matched_events)
                try:
                    ok = await email_service.send_email(
                        to_email=user.email,
                        subject="🚀 New Hackathons & Coding Contests",
                        html_content=html,
                        text_content=text,
                    )
                    if ok:
                        emails_sent += 1
                        profile.last_notification_time = datetime.now(timezone.utc)
                        db.add(profile)
                except Exception as e:
                    failures[f"email_{user.email}"] = str(e)[:200]
            
            await db.commit()

    end_time = datetime.now(timezone.utc)
    status = "failed" if len(failures) >= len(HOURLY_PLATFORMS) and HOURLY_PLATFORMS else "success"
    async with AsyncSessionLocal() as db:
        fresh_log = await db.get(SchedulerLog, log_id)
        if fresh_log:
            fresh_log.status = status
            fresh_log.completed_at = end_time
            fresh_log.duration_seconds = (end_time - start_time).total_seconds()
            fresh_log.events_found = events_found
            fresh_log.events_new = len(new_event_ids)
            fresh_log.emails_sent = emails_sent
            fresh_log.failures = failures
            db.add(fresh_log)
            await db.commit()

    summary = {
        "status": status,
        "events_found": events_found,
        "events_new": len(new_event_ids),
        "duplicates_removed": duplicates_removed,
        "emails_sent": emails_sent,
        "failures": failures,
    }
    logger.info("Hourly notification job finished", **summary)
    return summary
