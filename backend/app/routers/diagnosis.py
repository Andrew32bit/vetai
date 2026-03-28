"""
Diagnosis endpoints:
1. Photo upload → Vision LLM → skin/eye disease analysis
2. Lab results upload → OCR → structured data extraction via LLM
3. Diagnosis history
"""

import logging
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.hf_service import analyze_photo as hf_analyze_photo, interpret_lab_results
from app.services.usage_limiter import check_limit, increment, get_remaining

router = APIRouter()
logger = logging.getLogger(__name__)


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

        clinic_link = None
        if result.get("should_visit_vet") or result.get("severity") in ("medium", "high"):
            query = f"ветеринарная клиника {city}" if city else "ветеринарная клиника рядом"
            clinic_link = f"https://yandex.ru/maps/?text={query.replace(' ', '+')}"

        return PhotoDiagnosisResponse(
            condition=result.get("condition", "Не определено"),
            confidence=float(result.get("confidence", 0.0)),
            severity=result.get("severity", "medium"),
            description=result.get("description", ""),
            recommendation=result.get("recommendation", "Рекомендуем консультацию ветеринара."),
            should_visit_vet=result.get("should_visit_vet", True),
            clinic_link=clinic_link,
        )

    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        return PhotoDiagnosisResponse(
            condition="Ошибка анализа",
            confidence=0.0,
            severity="medium",
            description="Не удалось проанализировать фото. Попробуйте загрузить другое изображение.",
            recommendation="Рекомендуем показать питомца ветеринару для точной диагностики.",
            should_visit_vet=True,
            clinic_link="https://yandex.ru/maps/?text=ветеринарная+клиника+рядом",
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

    # TODO: integrate PaddleOCR for real text extraction
    # For now, use a placeholder OCR step
    file_bytes = await file.read()
    extracted_text = f"[OCR не подключён — файл {file.filename}, {len(file_bytes)} байт]"

    try:
        result = await interpret_lab_results(
            extracted_text=extracted_text,
            pet_species=species,
        )

        return LabResultsResponse(
            extracted_text=extracted_text,
            parsed_values=result.get("parsed_values", {}),
            anomalies=result.get("anomalies", []),
            summary=result.get("summary", "Не удалось интерпретировать результаты."),
        )

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
    # TODO: fetch from DB
    return {"items": [], "total": 0}
