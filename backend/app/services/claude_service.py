"""
Claude API integration for symptom chat and lab results interpretation.
"""

import anthropic
from app.config import get_settings


async def get_chat_response(
    messages: list[dict],
    system_prompt: str,
) -> str:
    """Send messages to Claude API and get response."""
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text


async def interpret_lab_results(
    extracted_text: str,
    pet_species: str,
    pet_age_months: int | None = None,
) -> dict:
    """
    Send OCR-extracted lab text to Claude for structured interpretation.
    Returns parsed values, anomalies, and summary.
    """
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)

    prompt = f"""Проанализируй результаты анализов домашнего животного.
Вид: {pet_species}
{f'Возраст: {pet_age_months} мес' if pet_age_months else ''}

Текст анализа (из OCR):
{extracted_text}

Верни JSON:
{{
  "parsed_values": {{"название_показателя": значение, ...}},
  "anomalies": ["описание отклонения 1", ...],
  "summary": "краткое резюме на русском"
}}"""

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    # TODO: parse JSON from response
    return {"raw": response.content[0].text}
