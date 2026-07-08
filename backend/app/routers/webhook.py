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


async def _store_pending_source(telegram_id: int, source: str):
    """Upsert acquisition source captured from /start, applied at /auth time."""
    try:
        from sqlalchemy import select
        from app.models.database import async_session, PendingAttribution
        async with async_session() as s:
            existing = (await s.execute(
                select(PendingAttribution).where(PendingAttribution.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if existing is None:
                s.add(PendingAttribution(telegram_id=telegram_id, source=source))
                await s.commit()
    except Exception as e:
        logger.error(f"Failed to store pending source: {e}")

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

HELP_RU = (
    "VetAI — ИИ-помощник для владельцев питомцев.\n\n"
    "Доступные функции:\n"
    "📸 Фото-диагностика — отправьте фото кожи, глаз или ушей питомца\n"
    "🔬 Расшифровка анализов — загрузите фото или PDF результатов\n"
    "💬 Чат с ветеринаром — опишите симптомы текстом\n\n"
    "Команды:\n"
    "/start — начать работу\n"
    "/help — справка\n"
    "/settings — настройки\n\n"
    "Нажмите кнопку ниже, чтобы открыть приложение."
    + DISCLAIMER_RU
)

HELP_EN = (
    "VetAI — AI-powered assistant for pet owners.\n\n"
    "Available features:\n"
    "📸 Photo diagnosis — send a photo of skin, eyes or ears\n"
    "🔬 Lab results — upload a photo or PDF of test results\n"
    "💬 Vet chat — describe symptoms in text\n\n"
    "Commands:\n"
    "/start — get started\n"
    "/help — this help message\n"
    "/settings — settings\n\n"
    "Tap the button below to open the app."
    + DISCLAIMER_EN
)

SETTINGS_RU = (
    "Настройки VetAI:\n\n"
    "Язык определяется автоматически из настроек Telegram.\n"
    "Лимит: 10 бесплатных запросов в день.\n\n"
    "Для изменения настроек откройте приложение."
)

SETTINGS_EN = (
    "VetAI Settings:\n\n"
    "Language is detected automatically from your Telegram settings.\n"
    "Limit: 10 free requests per day.\n\n"
    "Open the app to change settings."
)

FALLBACK_RU = (
    "Я понимаю только команды. Используйте приложение для общения с ветеринаром.\n\n"
    "Нажмите кнопку ниже или введите /help для справки."
)

FALLBACK_EN = (
    "I only understand commands. Use the app to chat with a vet.\n\n"
    "Tap the button below or type /help for assistance."
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

    if message.get("chat", {}).get("type") != "private":
        return {"ok": True}

    language = "ru" if lang.startswith("ru") else "en"

    # Handle /start command
    if text.startswith("/start"):
        # Capture acquisition source from deep-link param: /start src_<channel> or /start ref_<id>
        parts = text.split(maxsplit=1)
        param = parts[1].strip().lower() if len(parts) > 1 else ""
        if param and (param.startswith("src_") or param.startswith("ref")):
            source = "referral" if param.startswith("ref") else param[:40]
            user_id = user.get("id")
            if user_id:
                await _store_pending_source(user_id, source)
                logger.info(f"Captured source '{source}' for {user_id} via /start")
        welcome = WELCOME_RU if language == "ru" else WELCOME_EN
        send_user_message(chat_id, welcome, language)
        logger.info(f"Sent /start welcome to {chat_id} ({user.get('first_name', '?')})")

    # Handle /help command
    elif text.startswith("/help"):
        help_text = HELP_RU if language == "ru" else HELP_EN
        send_user_message(chat_id, help_text, language)
        logger.info(f"Sent /help to {chat_id}")

    # Handle /settings command
    elif text.startswith("/settings"):
        settings_text = SETTINGS_RU if language == "ru" else SETTINGS_EN
        send_user_message(chat_id, settings_text, language)
        logger.info(f"Sent /settings to {chat_id}")

    # Fallback for any other text message
    elif text:
        fallback = FALLBACK_RU if language == "ru" else FALLBACK_EN
        send_user_message(chat_id, fallback, language)
        logger.info(f"Sent fallback to {chat_id}")

    return {"ok": True}
