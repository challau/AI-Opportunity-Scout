"""Telegram bot service for notifications."""

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = structlog.get_logger()


class TelegramService:
    """Send notifications via Telegram Bot API."""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)),
        reraise=False,
    )
    async def _post_message(self, payload: dict) -> bool:
        """Internal POST to Telegram API with retry logic."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            logger.warning("Telegram send failed", status=resp.status_code, body=resp.text[:200])
            return False

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
    ) -> bool:
        """Send a message to a Telegram chat with retry."""
        if not self.token:
            logger.warning("Telegram bot not configured")
            return False

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        try:
            result = await self._post_message(payload)
            if result:
                logger.info("Telegram message sent", chat_id=chat_id)
            return result
        except Exception as e:
            logger.error("Telegram error after retries", error=str(e))
            return False

    def _format_opportunity(self, event: dict) -> str:
        """Format event as Telegram HTML message."""
        title = event.get("title", "Unknown")
        platform = event.get("platform", "").capitalize()
        event_type = event.get("event_type", "").replace("_", " ").title()
        prize = event.get("prize") or "No prize"
        deadline = event.get("registration_deadline", "Check website")
        summary = event.get("short_summary") or event.get("description", "")[:200]
        url = event.get("registration_url", "#")
        score = event.get("ai_score", 0)

        return f"""🚀 <b>New Opportunity Found!</b>

📌 <b>{title}</b>

🏷️ {platform} · {event_type}
💰 Prize: {prize}
⏰ Deadline: {deadline}
⭐ AI Score: {score:.0f}/100

📝 {summary}

👉 <a href="{url}">Register Now</a>

<i>— AI Opportunity Scout</i>"""

    async def send_opportunity(self, chat_id: str, event: dict) -> bool:
        """Send formatted opportunity notification."""
        text = self._format_opportunity(event)
        return await self.send_message(chat_id, text)

    async def send_daily_digest(
        self, chat_id: str, events: list, date_str: str
    ) -> bool:
        """Send a daily digest of top opportunities."""
        if not events:
            return True

        header = f"📅 <b>Daily Digest — {date_str}</b>\n\nTop opportunities for you today:\n\n"
        lines = []
        for i, event in enumerate(events[:5], 1):
            lines.append(
                f"{i}. <b>{event.get('title', '')[:50]}</b>\n"
                f"   {event.get('platform', '').capitalize()} · {event.get('prize') or 'No prize'}\n"
                f"   <a href='{event.get('registration_url', '#')}'>Register</a>"
            )

        text = header + "\n\n".join(lines)
        return await self.send_message(chat_id, text)

    async def send_deadline_reminder(self, chat_id: str, event: dict, days_left: int) -> bool:
        """Send deadline reminder."""
        text = (
            f"⏰ <b>Deadline Reminder!</b>\n\n"
            f"<b>{event.get('title', '')}</b> closes in <b>{days_left} day{'s' if days_left != 1 else ''}</b>!\n\n"
            f"👉 <a href='{event.get('registration_url', '#')}'>Register Now</a>"
        )
        return await self.send_message(chat_id, text)
