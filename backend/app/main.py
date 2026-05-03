"""
VetAI Backend — FastAPI
AI-powered pet health diagnosis: photo analysis, lab results OCR, symptom chat.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import diagnosis, chat, user, health, webhook

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


@app.on_event("shutdown")
async def shutdown():
    """Final backup on shutdown."""
    from app.services.db_backup import backup_db
    await backup_db()
