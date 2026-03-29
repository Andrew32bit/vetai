"""
VetAI Backend — FastAPI
AI-powered pet health diagnosis: photo analysis, lab results OCR, symptom chat.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import diagnosis, chat, user, health

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
        "http://localhost:5173",  # Vite dev
        "http://localhost:5174",
        "http://localhost:3000",
        settings.TELEGRAM_WEBAPP_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(health.router, tags=["health"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["diagnosis"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.on_event("startup")
async def startup():
    """Restore DB from backup, initialize tables, start periodic backup."""
    import asyncio
    from app.services.db_backup import restore_db, periodic_backup
    from app.models.database import init_db

    await restore_db()
    await init_db()
    asyncio.create_task(periodic_backup())


@app.on_event("shutdown")
async def shutdown():
    """Final backup on shutdown."""
    from app.services.db_backup import backup_db
    await backup_db()
