"""
Telegram alerting for production errors.
Sends notifications to admin when users hit errors.
Rate-limited to avoid spam. Errors also saved to DB.
"""

import time
import logging
import urllib.request
import json
from app.config import get_settings

logger = logging.getLogger(__name__)


async def log_error_to_db(
    error_type: str,
    message: str,
    feature: str | None = None,
    telegram_id: int | None = None,
):
    """Save error to error_log table."""
    try:
        from app.models.database import async_session, ErrorLog
        async with async_session() as session:
            entry = ErrorLog(
                error_type=error_type,
                feature=feature,
                message=message[:2000],
                telegram_id=telegram_id,
            )
            session.add(entry)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to log error to DB: {e}")

# Rate limit: max 1 alert per error type per 5 minutes
_last_alert: dict[str, float] = {}
ALERT_COOLDOWN = 300  # 5 minutes


def _should_alert(error_key: str) -> bool:
    """Check if we should send alert (rate limiting)."""
    now = time.time()
    last = _last_alert.get(error_key, 0)
    if now - last < ALERT_COOLDOWN:
        return False
    _last_alert[error_key] = now
    return True


def send_alert(
    error_type: str,
    error_message: str,
    user_telegram_id: int | None = None,
    feature: str | None = None,
    extra: str | None = None,
):
    """Send error alert to admin via Telegram bot."""
    error_key = f"{error_type}:{feature or 'unknown'}"
    if not _should_alert(error_key):
        return

    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Cannot send alert: TELEGRAM_BOT_TOKEN not set")
        return

    # Build alert message
    parts = [f"⚠️ <b>VetAI Alert</b>"]
    parts.append(f"<b>Тип:</b> {error_type}")
    if feature:
        parts.append(f"<b>Фича:</b> {feature}")
    if user_telegram_id:
        parts.append(f"<b>Юзер:</b> {user_telegram_id}")
    parts.append(f"<b>Ошибка:</b> <code>{error_message[:500]}</code>")
    if extra:
        parts.append(f"<b>Детали:</b> {extra}")
    parts.append(f"<b>Время:</b> {time.strftime('%H:%M:%S %d.%m.%Y')}")

    text = "\n".join(parts)

    try:
        data = json.dumps({
            "chat_id": settings.ADMIN_TELEGRAM_ID,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
