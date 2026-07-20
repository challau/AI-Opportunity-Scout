"""Email service using SMTP and Jinja2 templates."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = structlog.get_logger()

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f1a; color: #e2e8f0; }}
  .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 16px 16px 0 0; padding: 40px 30px; text-align: center; }}
  .header h1 {{ color: white; font-size: 24px; font-weight: 700; }}
  .header p {{ color: rgba(255,255,255,0.8); margin-top: 8px; }}
  .body {{ background: #1a1a2e; padding: 30px; }}
  .event-card {{ background: #252540; border: 1px solid #3a3a5c; border-radius: 12px; padding: 24px; margin: 20px 0; }}
  .event-title {{ font-size: 20px; font-weight: 700; color: #a78bfa; margin-bottom: 12px; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin: 4px 2px; }}
  .badge-platform {{ background: #312e81; color: #a5b4fc; }}
  .badge-type {{ background: #134e4a; color: #6ee7b7; }}
  .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #3a3a5c; }}
  .detail-label {{ color: #94a3b8; font-size: 14px; }}
  .detail-value {{ color: #e2e8f0; font-size: 14px; font-weight: 500; }}
  .summary {{ background: #1e1e38; border-left: 4px solid #6366f1; padding: 16px; margin: 16px 0; border-radius: 0 8px 8px 0; }}
  .cta-btn {{ display: block; width: fit-content; margin: 24px auto; padding: 14px 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 16px; }}
  .ai-reason {{ background: #0f2a1a; border: 1px solid #166534; border-radius: 8px; padding: 16px; margin: 16px 0; }}
  .ai-reason-title {{ color: #4ade80; font-size: 14px; font-weight: 600; margin-bottom: 8px; }}
  .footer {{ background: #0f0f1a; padding: 20px; text-align: center; color: #64748b; font-size: 12px; border-radius: 0 0 16px 16px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚀 AI Opportunity Scout</h1>
    <p>A new opportunity matches your profile!</p>
  </div>
  <div class="body">
    <p style="color: #94a3b8; margin-bottom: 20px;">Hi {user_name}, here's an opportunity we found for you:</p>
    <div class="event-card">
      <div class="event-title">{event_title}</div>
      <div>
        <span class="badge badge-platform">{platform}</span>
        <span class="badge badge-type">{event_type}</span>
      </div>
      <div style="margin-top: 16px;">
        <div class="detail-row"><span class="detail-label">💰 Prize</span><span class="detail-value">{prize}</span></div>
        <div class="detail-row"><span class="detail-label">⏰ Deadline</span><span class="detail-value">{deadline}</span></div>
        <div class="detail-row"><span class="detail-label">📍 Location</span><span class="detail-value">{location}</span></div>
      </div>
      <div class="summary">
        <strong style="color: #a78bfa;">AI Summary</strong><br>
        <p style="margin-top: 8px; color: #cbd5e1; line-height: 1.6;">{summary}</p>
      </div>
    </div>
    <div class="ai-reason">
      <div class="ai-reason-title">🤖 Why AI Recommends This</div>
      <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6;">{ai_reason}</p>
    </div>
    <a href="{registration_url}" class="cta-btn">Register Now →</a>
  </div>
  <div class="footer">
    <p>AI Opportunity Scout · <a href="#" style="color: #6366f1;">Manage Preferences</a> · <a href="#" style="color: #6366f1;">Unsubscribe</a></p>
  </div>
</div>
</body>
</html>
"""


class EmailService:
    """Sends transactional and notification emails."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiosmtplib.SMTPException, ConnectionError, OSError)),
        reraise=True,
    )
    async def _send_with_retry(self, msg, to_email: str) -> None:
        """Internal method with retry logic for SMTP delivery."""
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )

    async def _send_via_brevo_api(
        self, to_email: str, subject: str, html_content: str, text_content: Optional[str]
    ) -> bool:
        """Send via Brevo's HTTPS API — works where outbound SMTP ports are blocked."""
        import httpx

        payload = {
            "sender": {"name": settings.SMTP_FROM_NAME, "email": settings.SMTP_FROM_EMAIL},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        }
        if text_content:
            payload["textContent"] = text_content

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code in (200, 201):
            logger.info("Email sent via Brevo API", to=to_email, subject=subject)
            return True
        logger.error("Brevo API send failed", status=resp.status_code, body=resp.text[:200], to=to_email)
        return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email via Brevo HTTP API (preferred) or SMTP fallback."""
        # HTTPS API first: Railway blocks outbound SMTP ports
        if settings.BREVO_API_KEY:
            try:
                return await self._send_via_brevo_api(to_email, subject, html_content, text_content)
            except Exception as e:
                logger.error("Brevo API error, falling back to SMTP", error=str(e))

        if not settings.SMTP_USERNAME:
            logger.warning("SMTP not configured, skipping email")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            await self._send_with_retry(msg, to_email)
            logger.info("Email sent", to=to_email, subject=subject)
            return True
        except Exception as e:
            logger.error("Email failed after retries", error=str(e), to=to_email)
            return False

    async def send_opportunity_notification(
        self,
        user_name: str,
        to_email: str,
        event: dict,
        ai_reason: str = "This matches your interests and skill profile.",
    ) -> bool:
        """Send a beautiful HTML notification email for an event."""
        html = EMAIL_TEMPLATE.format(
            subject=f"New Opportunity: {event.get('title', '')}",
            user_name=user_name,
            event_title=event.get("title", ""),
            platform=event.get("platform", "").capitalize(),
            event_type=event.get("event_type", "").replace("_", " ").title(),
            prize=event.get("prize") or "Not specified",
            deadline=str(event.get("registration_deadline", "Check website")),
            location=event.get("location") or ("Remote" if event.get("is_remote") else "Check website"),
            summary=event.get("short_summary") or event.get("description", "")[:300],
            ai_reason=ai_reason,
            registration_url=event.get("registration_url", "#"),
        )
        return await self.send_email(
            to_email=to_email,
            subject=f"🚀 New Opportunity: {event.get('title', '')[:50]}",
            html_content=html,
        )

    async def send_password_reset(
        self, to_email: str, user_name: str, reset_url: str
    ) -> bool:
        """Send password reset email."""
        html = f"""
        <div style="font-family: Arial; max-width: 500px; margin: 0 auto; padding: 30px; background: #1a1a2e; color: #e2e8f0; border-radius: 12px;">
          <h2 style="color: #6366f1;">Password Reset</h2>
          <p>Hi {user_name},</p>
          <p>Click the button below to reset your password. This link expires in 1 hour.</p>
          <a href="{reset_url}" style="display: inline-block; margin: 20px 0; padding: 12px 24px; background: #6366f1; color: white; border-radius: 8px; text-decoration: none; font-weight: 600;">Reset Password</a>
          <p style="color: #64748b; font-size: 12px;">If you didn't request this, ignore this email.</p>
        </div>
        """
        return await self.send_email(to_email, "Reset Your Password - AI Opportunity Scout", html)
