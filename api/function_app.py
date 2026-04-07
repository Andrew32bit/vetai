"""
Azure Functions wrapper for VetAI FastAPI backend.
Uses azure.functions adapter to run FastAPI as Azure Function.
"""

import azure.functions as func
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.routers import diagnosis, chat, user, health

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-ветеринарный ассистент: диагностика по фото, OCR анализов, чат с ИИ",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["diagnosis"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.on_event("startup")
async def startup():
    """Initialize DB on startup."""
    from app.models.database import init_db
    await init_db()


# Azure Functions adapter
azure_function_app = func.AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.ANONYMOUS)


# Timer trigger: send 24h reminders to inactive users (runs every hour)
@azure_function_app.timer_trigger(schedule="0 0 * * * *", arg_name="timer", run_on_startup=False)
async def send_reminders(timer: func.TimerRequest) -> None:
    """Check for users registered 23-25h ago with 0 usage and send reminder."""
    import logging
    from datetime import datetime, timedelta
    from sqlalchemy import select, func as sqlfunc

    logger = logging.getLogger(__name__)
    logger.info("Reminder timer triggered")

    try:
        from app.models.database import async_session, User, UsageLog
        from app.services.alerting import send_reminder_message

        now = datetime.utcnow()
        window_start = now - timedelta(hours=25)
        window_end = now - timedelta(hours=23)

        async with async_session() as session:
            # Users with usage
            users_with_usage = (await session.execute(
                select(UsageLog.user_id).distinct()
            )).scalars().all()

            # Users registered 23-25h ago, no usage, reminder not sent
            query = (
                select(User)
                .where(User.created_at.between(window_start, window_end))
                .where(User.reminder_sent == False)
                .where(User.telegram_id != 12345)
            )
            if users_with_usage:
                query = query.where(User.id.notin_(users_with_usage))

            users = (await session.execute(query)).scalars().all()

            sent = 0
            for user in users:
                lang = user.language_code or "ru"
                result = send_reminder_message(user.telegram_id, lang)
                user.reminder_sent = True
                if result is True:
                    sent += 1
                    logger.info(f"Reminder sent to {user.telegram_id} ({user.first_name})")
                elif result is None:
                    logger.info(f"User {user.telegram_id} blocked the bot")
                else:
                    logger.warning(f"Failed to send reminder to {user.telegram_id}")

            await session.commit()
            logger.info(f"Reminder run complete: {sent}/{len(users)} sent")

    except Exception as e:
        logger.error(f"Reminder timer error: {e}")
