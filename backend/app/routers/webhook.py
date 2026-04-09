"""
Telegram Bot webhook handler.
Processes /start command and sends welcome message with Mini App button.
"""

import logging
from fastapi import APIRouter, Request
from app.config import get_settings
from app.services.alerting import send_user_message

router = APIRouter()
logger = logging.getLogger(__name__)

DISCLAIMER_RU = (
    "\n\n⚠️ VetAI — информационный сервис. Не является медицинской услугой, "
    "не ставит диагнозы и не назначает лечение. Результаты носят предварительный "
    "характер. Всегда консультируйтесь с лицензированным ветеринаром."
)

DISCLAIMER_EN = (
    "\n\n⚠️ VetAI is an informational tool only. It does not provide medical "
    "diagnoses, treatment or prescriptions. Results are preliminary assessments. "
    "Always consult a licensed veterinarian for professional advice."
)

WELCOME_RU = (
    "Привет! Я VetAI — ИИ-помощник для владельцев питомцев.\n\n"
    "Я помогу предварительно оценить состояние вашего питомца:\n"
    "📸 Фото — визуальный анализ кожи, глаз, ушей\n"
    "🔬 Анализы — расшифровка результатов из фото/PDF\n"
    "💬 Чат — описание симптомов\n\n"
    "Нажмите кнопку ниже, чтобы начать!"
    + DISCLAIMER_RU
)

WELCOME_EN = (
    "Hi! I'm VetAI — an AI-powered assistant for pet owners.\n\n"
    "I can help with a preliminary assessment of your pet's condition:\n"
    "📸 Photo — visual analysis of skin, eyes, ears\n"
    "🔬 Lab results — interpretation from photo/PDF\n"
    "💬 Chat — describe symptoms\n\n"
    "Tap the button below to get started!"
    + DISCLAIMER_EN
)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates."""
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message")
    if not message:
        return {"ok": True}

    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    user = message.get("from", {})
    lang = user.get("language_code", "ru")

    if not chat_id:
        return {"ok": True}

    # Handle /start command
    if text.startswith("/start"):
        language = "ru" if lang.startswith("ru") else "en"
        welcome = WELCOME_RU if language == "ru" else WELCOME_EN
        send_user_message(chat_id, welcome, language)
        logger.info(f"Sent /start welcome to {chat_id} ({user.get('first_name', '?')})")

    return {"ok": True}
