"""
Groq API integration for veterinary chat and photo/lab analysis.
Models: Llama 3.3 70B (chat), Llama 4 Scout (vision).
"""

import base64
import json
import re
import time
import logging
from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


async def get_chat_response(
    messages: list[dict],
    system_prompt: str,
) -> str:
    """Send messages to Groq chat model and get response."""
    settings = get_settings()
    client = _get_client()

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat.completions.create(
        model=settings.GROQ_CHAT_MODEL,
        messages=full_messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content


async def analyze_photo(
    image_bytes: bytes,
    pet_species: str,
    content_type: str = "image/jpeg",
    complaint: str | None = None,
) -> dict:
    """Analyze pet photo using Groq vision model."""
    settings = get_settings()
    client = _get_client()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{content_type};base64,{b64_image}"

    complaint_text = f"\nЖалоба владельца: {complaint}" if complaint else ""

    prompt = f"""Ты — опытный ветеринарный врач. Проанализируй фото.{complaint_text}

ШАГ 1: Определи, есть ли на фото животное.
- Если на фото НЕТ животного (человек, предмет, еда, пейзаж и т.д.) — верни:
{{"condition": "not_animal", "confidence": 0.0, "severity": "low", "description": "На фото не обнаружено животное.", "recommendation": "Пожалуйста, загрузите фото вашего питомца.", "should_visit_vet": false}}

ШАГ 2: Если животное есть, но видимых проблем нет — верни:
{{"condition": "healthy", "confidence": 0.9, "severity": "low", "description": "На фото животное выглядит здоровым, видимых проблем не обнаружено.", "recommendation": "Если вас что-то беспокоит, попробуйте загрузить фото проблемного участка крупным планом.", "should_visit_vet": false}}

ШАГ 3: Если есть видимая проблема — проанализируй как ветеринарный врач ({pet_species}).
ВАЖНО: Не спеши ставить диагноз «рана» или «травма». Сначала проанализируй характер поражения:
- Покраснение с мокнутием, эрозиями, без чётких краёв пореза — дерматит (аллергический, атопический, контактный)
- Пустулы и гной — пиодермия
- Округлая алопеция с шелушением — дерматофития (лишай)
- Локальная алопеция, покраснение, чешуйки — демодекоз
- Острое мокнущее воспаление — мокнущая экзема (горячая точка)
- Рана/травма — ТОЛЬКО если видны явные порезы, разрывы ткани с ровными краями

ЯЗЫК: Весь ответ СТРОГО на русском языке. Никаких английских терминов. Вместо "hot spot" пиши "мокнущая экзема", вместо "dermatitis" пиши "дерматит" и т.д.

Ответь СТРОГО в формате JSON:
{{"condition": "диагноз на русском", "confidence": 0.0-1.0, "severity": "low|medium|high", "description": "описание на русском", "recommendation": "рекомендации на русском", "should_visit_vet": true|false}}"""

    # Retry up to 3 times
    raw_text = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_uri}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=1024,
            )
            raw_text = response.choices[0].message.content
            break
        except Exception as e:
            logger.warning(f"Vision API attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2)

    if raw_text is None:
        raise RuntimeError("Vision API failed after 3 attempts")

    # Parse JSON from response
    try:
        json_match = re.search(r'\{[^{}]*\}', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "condition": "Не удалось определить",
        "confidence": 0.0,
        "severity": "medium",
        "description": raw_text,
        "recommendation": "Рекомендуем показать питомца ветеринару для точной диагностики.",
        "should_visit_vet": True,
    }


async def interpret_lab_results_image(
    image_bytes: bytes,
    pet_species: str,
    content_type: str = "image/jpeg",
) -> dict:
    """Read lab results from image using Groq vision model."""
    settings = get_settings()
    client = _get_client()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{content_type};base64,{b64_image}"

    prompt = f"""Ты — опытный ветеринарный врач. На фото результаты анализов {pet_species}.

ШАГ 1: Прочитай ВСЕ значения с фото (названия показателей и их числовые значения).
ШАГ 2: Определи, какие показатели выходят за пределы нормы для {pet_species}.
ШАГ 3: На основе совокупности отклонений предположи возможный диагноз или состояние.
ШАГ 4: Дай развёрнутое заключение на русском языке. В конце ОБЯЗАТЕЛЬНО добавь: "Данные результаты носят предварительный характер. Для точного диагноза и назначения лечения обратитесь к ветеринарному врачу."

Отвечай СТРОГО на русском. Ответь в формате JSON:
{{"extracted_text": "распознанный текст", "parsed_values": {{"показатель": "значение (норма: X-Y)", ...}}, "anomalies": ["отклонение 1", ...], "diagnosis": "предполагаемый диагноз", "summary": "развёрнутое заключение с рекомендацией обратиться к ветеринару"}}"""

    raw_text = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_uri}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=2048,
            )
            raw_text = response.choices[0].message.content
            break
        except Exception as e:
            logger.warning(f"Vision API attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2)

    if raw_text is None:
        return {"extracted_text": "", "parsed_values": {}, "anomalies": [], "summary": "Не удалось распознать анализы. Попробуйте загрузить более чёткое фото."}

    try:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {"extracted_text": raw_text, "parsed_values": {}, "anomalies": [], "summary": raw_text}
