"""
Symptom chat: structured conversation with HuggingFace LLM.
Collects symptoms → generates preliminary assessment → recommends clinic if urgent.
"""

import logging
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.hf_service import get_chat_response
from app.services.usage_limiter import check_limit, increment, get_remaining

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    pet_id: Optional[int] = None
    history: list[ChatMessage] = []
    city: Optional[str] = None  # город пользователя для рекомендации клиник


class ChatResponse(BaseModel):
    reply: str
    follow_up_questions: list[str] = []
    preliminary_assessment: Optional[str] = None
    urgency: Optional[str] = None  # "low" | "medium" | "high" | "emergency"
    clinic_recommendation: Optional[str] = None


SYSTEM_PROMPT = """ЯЗЫК: Ты ОБЯЗАН отвечать ИСКЛЮЧИТЕЛЬНО на русском языке. Запрещено использовать слова на английском, китайском или любом другом языке. Даже медицинские термины пиши по-русски. Например: "очень серьёзный" (НЕ "very serious"), "горячая точка" (НЕ "hot spot"). Если ты напишешь хоть одно слово не на русском — это критическая ошибка.

Ты — VetAI, AI-ассистент ветеринарного врача. Ты помогаешь владельцам домашних животных предварительно оценить симптомы их питомцев.

ПРАВИЛА:
- Ты НЕ ставишь окончательный диагноз — только предварительную оценку
- Задавай уточняющие вопросы для сбора анамнеза (возраст, порода, длительность симптомов, аппетит, активность)
- При подозрении на серьёзное состояние — рекомендуй срочный визит к ветврачу
- Будь доброжелательным и понятным
- Используй ветеринарную терминологию с пояснениями для владельцев

ФОРМАТ ОТВЕТА:
Всегда заканчивай ответ блоком в формате:
[URGENCY: low|medium|high|emergency]
[ASSESSMENT: краткая оценка или "нет" если недостаточно данных]
[QUESTIONS: вопрос 1 | вопрос 2]

Уровни срочности:
- low: состояние не вызывает опасений, можно наблюдать дома
- medium: стоит показать ветврачу в ближайшие 1-3 дня
- high: нужен визит к ветврачу сегодня
- emergency: требуется экстренная ветеринарная помощь НЕМЕДЛЕННО

ВАЖНО:
- Если симптомы указывают на high/emergency — ОБЯЗАТЕЛЬНО скажи об этом прямо и настоятельно рекомендуй визит к ветврачу
- ВСЕ части ответа, включая [QUESTIONS], ДОЛЖНЫ быть на русском языке. Ни одного слова на другом языке."""


def _parse_structured_response(text: str) -> dict:
    """Extract urgency, assessment, and questions from LLM response."""
    urgency = None
    assessment = None
    questions = []
    clean_reply = text

    for line in text.split("\n"):
        line_stripped = line.strip()
        if line_stripped.startswith("[URGENCY:"):
            val = line_stripped.replace("[URGENCY:", "").rstrip("]").strip().lower()
            if val in ("low", "medium", "high", "emergency"):
                urgency = val
            clean_reply = clean_reply.replace(line, "")
        elif line_stripped.startswith("[ASSESSMENT:"):
            val = line_stripped.replace("[ASSESSMENT:", "").rstrip("]").strip()
            if val.lower() != "нет":
                assessment = val
            clean_reply = clean_reply.replace(line, "")
        elif line_stripped.startswith("[QUESTIONS:"):
            val = line_stripped.replace("[QUESTIONS:", "").rstrip("]").strip()
            questions = [q.strip() for q in val.split("|") if q.strip()]
            clean_reply = clean_reply.replace(line, "")

    return {
        "reply": clean_reply.strip(),
        "urgency": urgency or "low",
        "assessment": assessment,
        "questions": questions,
    }


def _get_clinic_recommendation(urgency: str, city: str | None) -> str | None:
    """Generate clinic recommendation based on urgency and location."""
    if urgency not in ("high", "emergency"):
        return None

    if urgency == "emergency":
        prefix = "СРОЧНО! Вашему питомцу нужна экстренная помощь!"
    else:
        prefix = "Рекомендуем посетить ветеринарную клинику в ближайшее время."

    from urllib.parse import quote
    if city:
        maps_query = f"ветеринарная клиника {city}"
        maps_url = f"https://yandex.ru/maps/?text={quote(maps_query)}"
        return f"{prefix}\n\nНайти ближайшую клинику в г. {city}:\n{maps_url}"
    else:
        maps_url = f"https://yandex.ru/maps/?text={quote('ветеринарная клиника рядом')}"
        return f"{prefix}\n\nНайти ближайшую клинику:\n{maps_url}"


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    x_telegram_id: int = Header(...),
):
    """Send message to symptom chat via HuggingFace LLM."""
    if not await check_limit(x_telegram_id):
        remaining = await get_remaining(x_telegram_id)
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Лимит 3 запроса в день исчерпан. Попробуйте завтра.",
                "remaining": remaining,
            },
        )
    await increment(x_telegram_id, "chat")

    # Build conversation history for the model
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.message})

    try:
        raw_response = await get_chat_response(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
        )

        parsed = _parse_structured_response(raw_response)

        clinic_rec = _get_clinic_recommendation(
            parsed["urgency"], request.city
        )

        response = ChatResponse(
            reply=parsed["reply"],
            follow_up_questions=parsed["questions"],
            preliminary_assessment=parsed["assessment"],
            urgency=parsed["urgency"],
            clinic_recommendation=clinic_rec,
        )

        return response

    except Exception as e:
        logger.error(f"HuggingFace API error: {e}")
        return ChatResponse(
            reply="Извините, произошла ошибка при обработке запроса. Попробуйте ещё раз.",
            follow_up_questions=[],
            preliminary_assessment=None,
            urgency=None,
            clinic_recommendation=None,
        )
