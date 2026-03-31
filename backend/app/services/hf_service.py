"""
Groq API integration for veterinary chat and photo/lab analysis.
Models: Llama 3.3 70B (chat), Llama 4 Scout (vision).
Fallback: Claude API when Groq rate-limited (429).
"""

import base64
import json
import re
import time
import logging
from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)

# Track Groq rate limit state to avoid repeated failed calls
_groq_chat_limited_until: float = 0
_groq_vision_limited_until: float = 0

# Track which provider served the last request (for usage logging)
last_provider: str = "groq"


def _parse_json_response(text: str) -> dict | None:
    """Parse JSON from LLM response, handling ```json``` blocks."""
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\s*', '', text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    try:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


def _get_claude_client():
    """Get async Anthropic client."""
    import anthropic
    settings = get_settings()
    if not settings.CLAUDE_API_KEY:
        raise RuntimeError("Groq rate-limited and CLAUDE_API_KEY not configured")
    return anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)


async def _claude_chat_fallback(
    messages: list[dict],
    system_prompt: str,
) -> str:
    """Fallback to Claude API when Groq is rate-limited."""
    settings = get_settings()
    client = _get_claude_client()
    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


async def _claude_vision_fallback(
    b64_image: str,
    content_type: str,
    prompt: str,
    max_tokens: int = 1024,
) -> str:
    """Fallback to Claude Vision API when Groq vision is rate-limited."""
    settings = get_settings()
    client = _get_claude_client()
    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return response.content[0].text


async def get_chat_response(
    messages: list[dict],
    system_prompt: str,
) -> str:
    """Send messages to Groq, fallback to Claude on rate limit."""
    global _groq_chat_limited_until, last_provider
    settings = get_settings()

    # If Groq is known to be rate-limited, go straight to Claude
    if time.time() < _groq_chat_limited_until:
        logger.info("Groq chat rate-limited, using Claude fallback")
        last_provider = "claude"
        return await _claude_chat_fallback(messages, system_prompt)

    try:
        client = _get_client()
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=settings.GROQ_CHAT_MODEL,
            messages=full_messages,
            max_tokens=1024,
            temperature=0.7,
        )
        last_provider = "groq"
        return response.choices[0].message.content
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            _groq_chat_limited_until = time.time() + 300
            logger.warning("Groq chat rate-limited, switching to Claude for 5 min")
            last_provider = "claude"
            return await _claude_chat_fallback(messages, system_prompt)
        raise


def _photo_prompt(pet_species: str, complaint: str | None = None) -> str:
    """Build photo analysis prompt."""
    complaint_text = f"\nЖалоба владельца: {complaint}" if complaint else ""
    return f"""Ты — опытный ветеринарный врач. Проанализируй фото.{complaint_text}

ШАГ 1: Определи, есть ли на фото животное.
- Если на фото НЕТ животного (человек, предмет, еда, пейзаж и т.д.) — верни:
{{"condition": "не_животное", "confidence": 0.0, "severity": "низкая", "description": "На фото не обнаружено животное.", "recommendation": "Пожалуйста, загрузите фото вашего питомца.", "should_visit_vet": false}}

ШАГ 2: Проведи ДЕТАЛЬНЫЙ осмотр. Сначала перечисли ВСЁ что видишь на коже/шерсти/глазах/ушах перед тем как ставить оценку:
- Корочки, струпья, ранки, царапины, пятна, бугорки, папулы
- Покраснения, отёки, припухлости
- Участки без шерсти, проплешины
- Выделения из глаз, носа, ушей
- Тёмные точки (могут быть клещи, блохи, укусы насекомых)
- Изменения текстуры или цвета кожи
ВАЖНО: Даже МЕЛКИЕ корочки, тёмные точки или ранки — это НЕ норма. Владелец загрузил фото потому что его что-то беспокоит. Лучше перестраховаться.

Если после детального осмотра действительно НИЧЕГО подозрительного нет — condition="здоров".

ШАГ 3: Если обнаружена ЛЮБАЯ проблема — поставь КОНКРЕТНЫЙ предварительный диагноз как опытный ветеринарный врач ({pet_species}).

ДИАГНОСТИЧЕСКИЕ ПОДСКАЗКИ:
Кожа:
- Покраснение с мокнутием, эрозии → дерматит (аллергический, атопический, контактный)
- Пустулы и гной → пиодермия
- Округлая алопеция с шелушением → дерматофития (лишай)
- Локальная алопеция, покраснение, чешуйки → демодекоз
- Острое мокнущее воспаление → мокнущая экзема
- Множественные мелкие корочки, тёмные точки (особенно на голове/ушах) → укусы клещей (возможен пироплазмоз, боррелиоз/болезнь Лайма, эрлихиоз)
- Расчёсы, мелкие тёмные точки в шерсти → блошиный дерматит
- Рана/травма — ТОЛЬКО при явных порезах/разрывах ткани

Глаза: конъюнктивит, блефарит, кератит, увеит
Уши: отит (наружный/средний), отодектоз (ушной клещ), гематома ушной раковины
Нос: ринит, гиперкератоз
Ротовая полость: стоматит, гингивит, зубной камень

ВАЖНО: Ставь КОНКРЕТНЫЙ диагноз, а НЕ "подозрение на кожные повреждения" или "наблюдаются корочки". Владелец ждёт от тебя предварительное медицинское заключение.

ЯЗЫК: Весь ответ СТРОГО на русском языке. Никаких английских терминов.

Ответь СТРОГО в формате JSON:
{{"condition": "конкретный диагноз на русском", "confidence": 0.0-1.0, "severity": "низкая|средняя|высокая", "description": "что видно на фото + обоснование диагноза", "recommendation": "конкретные рекомендации по лечению и обследованию", "should_visit_vet": true|false}}"""


def _parse_vision_result(raw_text: str) -> dict:
    """Parse vision model response into structured dict."""
    parsed = _parse_json_response(raw_text)
    if parsed:
        return parsed
    return {
        "condition": "Не удалось определить",
        "confidence": 0.0,
        "severity": "средняя",
        "description": raw_text,
        "recommendation": "Рекомендуем показать питомца ветеринару для точной диагностики.",
        "should_visit_vet": True,
    }


async def analyze_photo(
    image_bytes: bytes,
    pet_species: str,
    content_type: str = "image/jpeg",
    complaint: str | None = None,
) -> dict:
    """Analyze pet photo: Groq vision → Claude vision fallback."""
    global _groq_vision_limited_until, last_provider
    settings = get_settings()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    prompt = _photo_prompt(pet_species, complaint)

    # If Groq vision is rate-limited, go straight to Claude
    if time.time() < _groq_vision_limited_until:
        logger.info("Groq vision rate-limited, using Claude vision fallback")
        raw_text = await _claude_vision_fallback(b64_image, content_type, prompt)
        last_provider = "claude"
        return _parse_vision_result(raw_text)

    # Try Groq vision
    data_uri = f"data:{content_type};base64,{b64_image}"
    raw_text = None
    use_claude = False

    for attempt in range(3):
        try:
            client = _get_client()
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
            last_provider = "groq"
            break
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                _groq_vision_limited_until = time.time() + 300
                logger.warning("Groq vision rate-limited, switching to Claude vision for 5 min")
                use_claude = True
                break
            logger.warning(f"Vision API attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2)

    # Fallback to Claude vision
    if use_claude or raw_text is None:
        raw_text = await _claude_vision_fallback(b64_image, content_type, prompt)
        last_provider = "claude"

    return _parse_vision_result(raw_text)


async def interpret_lab_results_image(
    image_bytes: bytes,
    pet_species: str,
    content_type: str = "image/jpeg",
) -> dict:
    """Read lab results from image: Groq vision → Claude vision fallback."""
    global _groq_vision_limited_until, last_provider
    settings = get_settings()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""Ты — опытный ветеринарный врач. На фото результаты анализов {pet_species}.

ШАГ 1: Прочитай ВСЕ значения с фото (названия показателей и их числовые значения).
ШАГ 2: Определи, какие показатели выходят за пределы нормы для {pet_species}.
ШАГ 3: На основе совокупности отклонений предположи возможный диагноз или состояние.
ШАГ 4: Дай развёрнутое заключение на русском языке. В конце ОБЯЗАТЕЛЬНО добавь: "Данные результаты носят предварительный характер. Для точного диагноза и назначения лечения обратитесь к ветеринарному врачу."

Отвечай СТРОГО на русском. Ответь в формате JSON:
{{"extracted_text": "распознанный текст", "parsed_values": {{"показатель": "значение (норма: X-Y)", ...}}, "anomalies": ["отклонение 1", ...], "diagnosis": "предполагаемый диагноз", "summary": "развёрнутое заключение с рекомендацией обратиться к ветеринару"}}"""

    fallback = {"extracted_text": "", "parsed_values": {}, "anomalies": [], "summary": "Не удалось распознать анализы. Попробуйте загрузить более чёткое фото."}

    # If Groq vision is rate-limited, go straight to Claude
    if time.time() < _groq_vision_limited_until:
        logger.info("Groq vision rate-limited, using Claude vision for lab results")
        raw_text = await _claude_vision_fallback(b64_image, content_type, prompt, max_tokens=2048)
        last_provider = "claude"
        return _parse_json_response(raw_text) or {"extracted_text": raw_text, "parsed_values": {}, "anomalies": [], "summary": raw_text}

    # Try Groq vision
    data_uri = f"data:{content_type};base64,{b64_image}"
    raw_text = None
    use_claude = False

    for attempt in range(3):
        try:
            client = _get_client()
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
            last_provider = "groq"
            break
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                _groq_vision_limited_until = time.time() + 300
                logger.warning("Groq vision rate-limited, switching to Claude vision for 5 min")
                use_claude = True
                break
            logger.warning(f"Vision API attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2)

    # Fallback to Claude vision
    if use_claude or raw_text is None:
        try:
            raw_text = await _claude_vision_fallback(b64_image, content_type, prompt, max_tokens=2048)
            last_provider = "claude"
        except Exception as e:
            logger.error(f"Claude vision fallback failed: {e}")
            return fallback

    parsed = _parse_json_response(raw_text)
    if parsed:
        return parsed

    return {"extracted_text": raw_text, "parsed_values": {}, "anomalies": [], "summary": raw_text}
