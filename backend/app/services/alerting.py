"""
Telegram alerting for production errors and traffic events.
Sends notifications to admin when users hit errors or milestones.
Rate-limited to avoid spam. Errors also saved to DB.
"""

import time
import logging
import urllib.request
import json
from app.config import get_settings

logger = logging.getLogger(__name__)

# Traffic milestone tracking
_milestones_sent: set[int] = set()
MILESTONES = [10, 25, 50, 100, 200, 500, 1000]


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


def send_new_user_alert(
    first_name: str,
    username: str | None,
    city: str | None,
    language: str | None,
    total_users: int,
):
    """Alert admin about new user registration."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    user_str = f"@{username}" if username else first_name
    city_str = city or "—"
    lang_str = language or "—"

    text = (
        f"👤 <b>Новый пользователь #{total_users}</b>\n"
        f"<b>Имя:</b> {first_name}\n"
        f"<b>Username:</b> {user_str}\n"
        f"<b>Город:</b> {city_str}\n"
        f"<b>Язык:</b> {lang_str}\n"
        f"<b>Время:</b> {time.strftime('%H:%M:%S %d.%m.%Y')}"
    )

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
        logger.error(f"Failed to send new user alert: {e}")

    # Check milestones
    for m in MILESTONES:
        if total_users >= m and m not in _milestones_sent:
            _milestones_sent.add(m)
            _send_milestone_alert(m, total_users)


def _send_milestone_alert(milestone: int, total: int):
    """Alert admin about user milestone."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    text = f"🎉 <b>Milestone!</b> Уже <b>{total}</b> пользователей! (порог: {milestone})"

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
        logger.error(f"Failed to send milestone alert: {e}")


# --- User-facing messages ---

MINIAPP_URL = "https://t.me/vetai_app_bot"

# Rate limit for broadcasts: max 1 per hour
_last_broadcast: float = 0
BROADCAST_COOLDOWN = 3600


def send_user_message(telegram_id: int, text: str, language: str = "ru") -> bool:
    """Send a message to a user via Telegram Bot API with Mini App button.
    Returns True on success, False on failure. Returns None if user blocked the bot."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Cannot send message: TELEGRAM_BOT_TOKEN not set")
        return False

    button_text = "Открыть VetAI" if language.startswith("ru") else "Open VetAI"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": button_text, "url": MINIAPP_URL}
            ]]
        },
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 403:
            logger.info(f"User {telegram_id} blocked the bot")
            return None
        logger.error(f"Failed to send message to {telegram_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send message to {telegram_id}: {e}")
        return False


def send_welcome_message(telegram_id: int, language_code: str = "ru"):
    """Send welcome message after onboarding with CTA to try photo diagnosis."""
    if language_code.startswith("ru"):
        text = (
            "Отлично! Всё готово 🐾\n\n"
            "Попробуйте сфотографировать глаза, уши или кожу питомца — "
            "VetAI даст предварительную оценку за 30 секунд. Это бесплатно!"
        )
    else:
        text = (
            "All set! 🐾\n\n"
            "Try taking a photo of your pet's eyes, ears, or skin — "
            "VetAI will give you a preliminary assessment in 30 seconds. It's free!"
        )
    return send_user_message(telegram_id, text, language_code)


def send_reminder_message(telegram_id: int, language_code: str = "ru"):
    """Send 24h reminder to users who registered but never made a request."""
    if language_code.startswith("ru"):
        text = (
            "Привет! Попробуйте сфотографировать глаза, уши или кожу питомца — "
            "VetAI даст предварительную оценку за 30 секунд. Это бесплатно 🐾"
        )
    else:
        text = (
            "Hi! Try taking a photo of your pet's eyes, ears, or skin — "
            "VetAI will give you a preliminary assessment in 30 seconds. It's free 🐾"
        )
    return send_user_message(telegram_id, text, language_code)
