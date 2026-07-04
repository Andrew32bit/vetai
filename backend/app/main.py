"""
VetAI Backend — FastAPI
AI-powered pet health diagnosis: photo analysis, lab results OCR, symptom chat.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import diagnosis, chat, user, health, webhook, analytics

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-ветеринарный ассистент: диагностика по фото, OCR анализов, чат с ИИ",
)

# CORS — разрешаем Telegram Mini App и localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://andrew32bit.github.io",
        "https://salmon-hill-0a38f9b10.1.azurestaticapps.net",
        "https://kombatdrew-vetai-backend.hf.space",
        "http://localhost:5173",
        "http://localhost:5174",
        settings.TELEGRAM_WEBAPP_URL,
    ],
    allow_origin_regex=r"https://.*\.(pages\.dev|hf\.space)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(health.router, tags=["health"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["diagnosis"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(webhook.router, tags=["webhook"])


@app.on_event("startup")
async def startup():
    """Restore DB from backup, initialize tables, start periodic backup."""
    import asyncio
    from app.services.db_backup import restore_db, periodic_backup
    from app.models.database import init_db

    await restore_db()
    await init_db()
    asyncio.create_task(periodic_backup())
    asyncio.create_task(_keep_alive())
    asyncio.create_task(_reminder_loop())
    _register_webhook()


def _public_base_url() -> str:
    """Resolve public URL: BASE_URL env var, or HF Space subdomain, or empty."""
    import os
    if base := os.environ.get("BASE_URL"):
        return base.rstrip("/")
    space_id = os.environ.get("SPACE_ID")  # set by HF: e.g. "kombatDrew/vetai-backend"
    if space_id:
        owner, name = space_id.split("/", 1)
        return f"https://{owner.lower()}-{name.lower()}.hf.space"
    return ""


def _register_webhook():
    """Register Telegram webhook on startup."""
    import urllib.request
    import json as _json
    import logging
    _logger = logging.getLogger(__name__)
    try:
        _settings = get_settings()
        if not _settings.TELEGRAM_BOT_TOKEN:
            return
        base = _public_base_url()
        if not base:
            _logger.warning("BASE_URL/SPACE_ID not set — skipping webhook registration")
            return
        webhook_url = f"{base}/webhook"
        data = _json.dumps({"url": webhook_url}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{_settings.TELEGRAM_BOT_TOKEN}/setWebhook",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        _logger.info(f"Webhook registered at {webhook_url}: {resp.read().decode()}")
    except Exception as e:
        _logger.error(f"Failed to register webhook: {e}")


async def _keep_alive():
    """Ping self every 10 min to prevent free tier from sleeping."""
    import asyncio
    import urllib.request
    import logging
    logger = logging.getLogger(__name__)
    base = _public_base_url()
    if not base:
        logger.info("BASE_URL/SPACE_ID not set — keep-alive disabled")
        return
    url = f"{base}/health"
    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            urllib.request.urlopen(url, timeout=10)
        except Exception as e:
            logger.debug(f"Keep-alive ping failed: {e}")


async def _reminder_loop():
    """Re-engage users who registered/were active but went quiet (retention loop).

    Sends at most one reminder per user per REMINDER_INTERVAL. Gated behind the
    REMINDERS_ENABLED env flag (default off) so deploying the capability never
    spams real users until it's explicitly turned on. Sends run off the event
    loop via a thread to avoid blocking the single Uvicorn worker.
    """
    import os
    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    if os.environ.get("REMINDERS_ENABLED", "").lower() not in ("1", "true", "yes"):
        logger.info("Reminder loop disabled (set REMINDERS_ENABLED=1 to enable)")
        return

    from datetime import datetime, timedelta
    from sqlalchemy import select, or_
    from app.models.database import async_session, User
    from app.services.alerting import send_reminder_message

    BATCH = 40                      # cap sends per cycle (Telegram-friendly)
    INACTIVE_AFTER = timedelta(hours=24)
    REMINDER_COOLDOWN = timedelta(hours=72)

    while True:
        await asyncio.sleep(6 * 3600)  # every 6 hours
        try:
            now = datetime.utcnow()
            async with async_session() as session:
                rows = (await session.execute(
                    select(User).where(
                        User.last_login < now - INACTIVE_AFTER,
                        or_(User.last_reminder_at.is_(None),
                            User.last_reminder_at < now - REMINDER_COOLDOWN),
                    ).limit(BATCH)
                )).scalars().all()

                for user in rows:
                    lang = user.language_code or "ru"
                    result = await asyncio.to_thread(
                        send_reminder_message, user.telegram_id, lang
                    )
                    if result is not None:  # None == user blocked the bot
                        user.last_reminder_at = now
                    await asyncio.sleep(0.2)  # gentle pacing
                await session.commit()
                if rows:
                    logger.info(f"Reminder loop: attempted {len(rows)} re-engagement messages")
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Final backup on shutdown."""
    from app.services.db_backup import backup_db
    await backup_db()
