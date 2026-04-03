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
