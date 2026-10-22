import asyncio
import logging
import smtplib
from email.message import EmailMessage
from html import escape

from app.config import settings

logger = logging.getLogger("job_agent.email")


def _send_sync(to: str, subject: str, text: str, html: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.default_from_email or settings.email_host_user
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.email_host, settings.email_port, timeout=20) as smtp:
        if settings.email_use_tls:
            smtp.starttls()
        smtp.login(settings.email_host_user, settings.email_host_password)
        smtp.send_message(msg)


async def send_email(to: str, subject: str, text: str, html: str) -> bool:
    if not settings.smtp_enabled:
        logger.warning("SMTP not configured — email to %s not sent. Subject: %s\n%s", to, subject, text)
        return False
    try:
        await asyncio.to_thread(_send_sync, to, subject, text, html)
        return True
    except Exception:  # noqa: BLE001 — never leak SMTP errors to API callers
        logger.exception("Failed to send email to %s", to)
        return False


_PURPOSE_COPY = {
    "verify_email": ("Verify your email", "Use this code to verify your JobAgent AI account."),
    "reset_password": ("Reset your password", "Use this code to reset your JobAgent AI password."),
}


async def send_otp_email(to: str, code: str, purpose: str) -> bool:
    title, intro = _PURPOSE_COPY.get(purpose, ("Your verification code", "Your code:"))
    minutes = max(1, settings.otp_expiry_seconds // 60)
    text = f"{intro}\n\nCode: {code}\n\nIt expires in {minutes} minutes. If you didn't request this, ignore this email."
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:12px">
      <h2 style="color:#4f46e5;margin:0 0 8px">JobAgent AI — {escape(title)}</h2>
      <p style="color:#374151">{escape(intro)}</p>
      <p style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#111827;margin:24px 0">{escape(code)}</p>
      <p style="color:#6b7280;font-size:13px">This code expires in {minutes} minutes.
      If you didn't request it, you can safely ignore this email.</p>
    </div>"""
    sent = await send_email(to, f"JobAgent AI — {title}", text, html)
    if not sent and not settings.is_production:
        # Dev convenience so the flow can be tested without SMTP
        logger.warning("[DEV] OTP for %s (%s): %s", to, purpose, code)
    return sent
