"""
Diagnosis endpoints:
1. Photo upload → Vision LLM → skin/eye disease analysis
2. Lab results upload → OCR → structured data extraction via LLM
3. Diagnosis history
"""

import json
import logging
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select

from app.services.hf_service import analyze_photo as hf_analyze_photo, interpret_lab_results_image
from app.services.usage_limiter import check_limit, increment, get_remaining
from app.models.database import async_session, User, Diagnosis

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_user_id(telegram_id: int) -> int | None:
    """Look up internal user ID from telegram_id."""
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        row = result.scalar_one_or_none()
        return row


async def _save_diagnosis(
    telegram_id: int,
    dtype: str,
    condition: str | None = None,
    confidence: float | None = None,
    severity: str | None = None,
    result_json: dict | None = None,
):
    """Save a diagnosis record to the DB."""
    user_id = await _get_user_id(telegram_id)
    if user_id is None:
        logger.warning(f"Cannot save diagnosis: user {telegram_id} not found in DB")
        return
    async with async_session() as session:
        diag = Diagnosis(
            user_id=user_id,
            type=dtype,
            condition=condition,
            confidence=confidence,
            severity=severity,
            result_json=json.dumps(result_json, ensure_ascii=False) if result_json else None,
        )
        session.add(diag)
        await session.commit()


class PhotoDiagnosisResponse(BaseModel):
    condition: str
    confidence: float
    severity: str  # "low" | "medium" | "high"
    description: str
    recommendation: str
    should_visit_vet: bool
    clinic_link: Optional[str] = None


class LabResultsResponse(BaseModel):
    extracted_text: str
    parsed_values: dict
    anomalies: list
    summary: str


# --- Photo Analysis ---

@router.post("/photo", response_model=PhotoDiagnosisResponse)
async def analyze_photo(
    photo: UploadFile = File(...),
    pet_id: Optional[int] = None,
    species: str = "питомца",
    city: Optional[str] = None,
    x_telegram_id: int = Header(...),
):
    """Upload pet photo → HuggingFace Vision LLM analysis."""
    if not await check_limit(x_telegram_id):
        remaining = await get_remaining(x_telegram_id)
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Лимит 3 запроса в день исчерпан. Попробуйте завтра.",
                "remaining": remaining,
            },
        )
    await increment(x_telegram_id, "photo")

    try:
        image_bytes = await photo.read()
        content_type = photo.content_type or "image/jpeg"

        result = await hf_analyze_photo(
            image_bytes=image_bytes,
            pet_species=species,
            content_type=content_type,
        )

        # Handle non-animal photos
        if result.get("condition") == "not_animal":
            return PhotoDiagnosisResponse(
                condition="not_animal",
                confidence=0.0,
                severity="low",
                description="На фото не обнаружено животное.",
                recommendation="Пожалуйста, загрузите фото вашего питомца.",
                should_visit_vet=False,
            )

        # Handle healthy animal photos
        if result.get("condition") == "healthy":
            return PhotoDiagnosisResponse(
                condition="healthy",
                confidence=float(result.get("confidence", 0.9)),
                severity="low",
                description="На фото животное выглядит здоровым, видимых проблем не обнаружено.",
                recommendation="Если вас что-то беспокоит, попробуйте загрузить фото проблемного участка крупным планом.",
                should_visit_vet=False,
            )

        from urllib.parse import quote
        clinic_link = None
        if result.get("should_visit_vet") or result.get("severity") in ("medium", "high"):
            query = f"ветеринарная клиника {city}" if city else "ветеринарная клиника рядом"
            clinic_link = f"https://yandex.ru/maps/?text={quote(query)}"

        response = PhotoDiagnosisResponse(
            condition=result.get("condition", "Не определено"),
            confidence=float(result.get("confidence", 0.0)),
            severity=result.get("severity", "medium"),
            description=result.get("description", ""),
            recommendation=result.get("recommendation", "Рекомендуем консультацию ветеринара."),
            should_visit_vet=result.get("should_visit_vet", True),
            clinic_link=clinic_link,
        )

        # Save diagnosis to DB
        try:
            await _save_diagnosis(
                telegram_id=x_telegram_id,
                dtype="photo",
                condition=response.condition,
                confidence=response.confidence,
                severity=response.severity,
                result_json={
                    "condition": response.condition,
                    "confidence": response.confidence,
                    "severity": response.severity,
                    "description": response.description,
                    "recommendation": response.recommendation,
                },
            )
        except Exception as save_err:
            logger.error(f"Failed to save photo diagnosis: {save_err}")

        return response

    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        return PhotoDiagnosisResponse(
            condition="Ошибка анализа",
            confidence=0.0,
            severity="medium",
            description="Не удалось проанализировать фото. Попробуйте загрузить другое изображение.",
            recommendation="Рекомендуем показать питомца ветеринару для точной диагностики.",
            should_visit_vet=True,
            clinic_link="https://yandex.ru/maps/?text=%D0%B2%D0%B5%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B0%D1%80%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%BB%D0%B8%D0%BD%D0%B8%D0%BA%D0%B0%20%D1%80%D1%8F%D0%B4%D0%BE%D0%BC",
        )


# --- Lab Results ---

@router.post("/lab-results", response_model=LabResultsResponse)
async def analyze_lab_results(
    file: UploadFile = File(...),
    pet_id: Optional[int] = None,
    species: str = "питомца",
    x_telegram_id: int = Header(...),
):
    """Upload lab results photo/PDF → OCR → LLM interpretation."""
    if not await check_limit(x_telegram_id):
        remaining = await get_remaining(x_telegram_id)
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Лимит 3 запроса в день исчерпан. Попробуйте завтра.",
                "remaining": remaining,
            },
        )
    await increment(x_telegram_id, "lab")

    file_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"

    try:
        result = await interpret_lab_results_image(
            image_bytes=file_bytes,
            pet_species=species,
            content_type=content_type,
        )

        response = LabResultsResponse(
            extracted_text=result.get("extracted_text", ""),
            parsed_values=result.get("parsed_values", {}),
            anomalies=result.get("anomalies", []),
            summary=result.get("summary", "Не удалось интерпретировать результаты."),
        )

        # Save diagnosis to DB
        try:
            await _save_diagnosis(
                telegram_id=x_telegram_id,
                dtype="lab_results",
                condition="Анализы",
                result_json={
                    "extracted_text": response.extracted_text,
                    "parsed_values": response.parsed_values,
                    "anomalies": response.anomalies,
                    "summary": response.summary,
                },
            )
        except Exception as save_err:
            logger.error(f"Failed to save lab diagnosis: {save_err}")

        return response

    except Exception as e:
        logger.error(f"Lab results analysis error: {e}")
        return LabResultsResponse(
            extracted_text=extracted_text,
            parsed_values={},
            anomalies=[],
            summary="Ошибка при анализе. Попробуйте загрузить более чёткое изображение.",
        )


# --- Diagnosis History ---

@router.get("/history")
async def get_diagnosis_history(
    x_telegram_id: int = Header(...),
    limit: int = 20,
):
    """Get user's diagnosis history."""
    user_id = await _get_user_id(x_telegram_id)
    if user_id is None:
        return {"items": [], "total": 0}

    async with async_session() as session:
        result = await session.execute(
            select(Diagnosis)
            .where(Diagnosis.user_id == user_id)
            .order_by(Diagnosis.created_at.desc())
            .limit(limit)
        )
        diagnoses = result.scalars().all()

    items = []
    for d in diagnoses:
        items.append({
            "id": d.id,
            "type": d.type,
            "condition": d.condition,
            "confidence": d.confidence,
            "severity": d.severity,
            "result_json": json.loads(d.result_json) if d.result_json else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    return {"items": items, "total": len(items)}
