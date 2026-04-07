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

from app.services import hf_service
from app.services.hf_service import AllProvidersDownError
from app.services.hf_service import analyze_photo as hf_analyze_photo, interpret_lab_results_image
from app.services.usage_limiter import check_limit, increment, get_remaining
from app.services.alerting import send_alert, log_error_to_db
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
    try:
        user_id = await _get_user_id(telegram_id)
        if user_id is None:
            logger.warning(f"Cannot save diagnosis: user {telegram_id} not found in DB")
            await log_error_to_db("save_diagnosis_error", f"user {telegram_id} not found", feature=dtype, telegram_id=telegram_id)
            return
        async with async_session() as session:
            diag = Diagnosis(
                user_id=user_id,
                type=dtype,
                condition=condition,
                confidence=float(confidence) if confidence is not None else None,
                severity=severity,
                result_json=json.dumps(result_json, ensure_ascii=False) if result_json else None,
            )
            session.add(diag)
            await session.commit()
            await session.refresh(diag)
            logger.info(f"Diagnosis saved: id={diag.id} user={telegram_id} type={dtype} condition={condition}")
            return diag.id
    except Exception as e:
        logger.error(f"_save_diagnosis failed: {e}")
        await log_error_to_db("save_diagnosis_error", f"{dtype}: {e}", feature=dtype, telegram_id=telegram_id)
    return None


class PhotoDiagnosisResponse(BaseModel):
    condition: str
    confidence: float
    severity: str  # "низкая" | "средняя" | "высокая"
    description: str
    recommendation: str
    should_visit_vet: bool
    clinic_link: Optional[str] = None
    diagnosis_id: Optional[int] = None


class LabResultsResponse(BaseModel):
    extracted_text: str
    parsed_values: dict
    anomalies: list
    summary: str
    diagnosis_id: Optional[int] = None


# --- Photo Analysis ---

@router.post("/photo", response_model=PhotoDiagnosisResponse)
async def analyze_photo(
    photo: UploadFile = File(...),
    pet_id: Optional[int] = None,
    species: str = "питомца",
    complaint: Optional[str] = None,
    city: Optional[str] = None,
    language: str = "ru",
    x_telegram_id: int = Header(...),
):
    """Upload pet photo → HuggingFace Vision LLM analysis."""
    if not await check_limit(x_telegram_id):
        remaining = await get_remaining(x_telegram_id)
        msg = "Daily limit of 3 requests reached. Try again tomorrow." if language == "en" else "Лимит 3 запроса в день исчерпан. Попробуйте завтра."
        raise HTTPException(
            status_code=429,
            detail={
                "message": msg,
                "remaining": remaining,
            },
        )
    try:
        image_bytes = await photo.read()
        content_type = photo.content_type or "image/jpeg"

        result = await hf_analyze_photo(
            image_bytes=image_bytes,
            pet_species=species,
            content_type=content_type,
            complaint=complaint,
            language=language,
        )
        await increment(x_telegram_id, "photo", provider="groq")

        # Handle non-animal photos
        if result.get("condition") in ("не_животное", "not_animal"):
            if language == "en":
                resp = PhotoDiagnosisResponse(
                    condition="not_animal",
                    confidence=0.0,
                    severity="low",
                    description="No animal was found in the photo.",
                    recommendation="Please upload a photo of your pet.",
                    should_visit_vet=False,
                )
            else:
                resp = PhotoDiagnosisResponse(
                    condition="не_животное",
                    confidence=0.0,
                    severity="низкая",
                    description="На фото не обнаружено животное.",
                    recommendation="Пожалуйста, загрузите фото вашего питомца.",
                    should_visit_vet=False,
                )
            diag_id = await _save_diagnosis(telegram_id=x_telegram_id, dtype="photo", condition=resp.condition, severity=resp.severity)
            resp.diagnosis_id = diag_id
            return resp

        # Handle healthy animal photos
        if result.get("condition") in ("здоров", "healthy"):
            if language == "en":
                resp = PhotoDiagnosisResponse(
                    condition="healthy",
                    confidence=float(result.get("confidence", 0.9)),
                    severity="low",
                    description="The animal in the photo appears healthy, no visible problems detected.",
                    recommendation="If something concerns you, try uploading a close-up photo of the problem area.",
                    should_visit_vet=False,
                )
            else:
                resp = PhotoDiagnosisResponse(
                    condition="здоров",
                    confidence=float(result.get("confidence", 0.9)),
                    severity="низкая",
                    description="На фото животное выглядит здоровым, видимых проблем не обнаружено.",
                    recommendation="Если вас что-то беспокоит, попробуйте загрузить фото проблемного участка крупным планом.",
                    should_visit_vet=False,
                )
            diag_id = await _save_diagnosis(telegram_id=x_telegram_id, dtype="photo", condition=resp.condition, confidence=float(result.get("confidence", 0.9)), severity=resp.severity)
            resp.diagnosis_id = diag_id
            return resp

        from urllib.parse import quote
        clinic_link = None
        severity_trigger = ("средняя", "высокая", "medium", "high")
        if result.get("should_visit_vet") or result.get("severity") in severity_trigger:
            if language == "en":
                query = f"veterinary clinic {city}" if city else "veterinary clinic near me"
                clinic_link = f"https://www.google.com/maps/search/{quote(query)}"
            else:
                query = f"ветеринарная клиника {city}" if city else "ветеринарная клиника рядом"
                clinic_link = f"https://yandex.ru/maps/?text={quote(query)}"

        response = PhotoDiagnosisResponse(
            condition=result.get("condition", "Could not determine" if language == "en" else "Не определено"),
            confidence=float(result.get("confidence", 0.0)),
            severity=result.get("severity", "medium" if language == "en" else "средняя"),
            description=result.get("description", ""),
            recommendation=result.get("recommendation", "We recommend consulting a veterinarian." if language == "en" else "Рекомендуем консультацию ветеринара."),
            should_visit_vet=result.get("should_visit_vet", True),
            clinic_link=clinic_link,
        )

        # Save diagnosis to DB
        try:
            diag_id = await _save_diagnosis(
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
            response.diagnosis_id = diag_id
        except Exception as save_err:
            logger.error(f"Failed to save photo diagnosis: {save_err}")
            await log_error_to_db("save_diagnosis_error", f"photo: {save_err}", feature="photo", telegram_id=x_telegram_id)

        return response

    except AllProvidersDownError:
        logger.error("All AI providers are down (photo)")
        await log_error_to_db("all_providers_down", "Groq и Claude оба недоступны", feature="photo", telegram_id=x_telegram_id)
        if language == "en":
            return PhotoDiagnosisResponse(
                condition="High demand",
                confidence=0.0,
                severity="medium",
                description="We're experiencing high demand right now! We're scaling up our servers. Please try again in 5-10 minutes.",
                recommendation="Please try again in a few minutes.",
                should_visit_vet=False,
            )
        return PhotoDiagnosisResponse(
            condition="Высокая нагрузка",
            confidence=0.0,
            severity="средняя",
            description="Сейчас очень много пользователей! Мы срочно масштабируем серверы. Попробуйте через 5-10 минут.",
            recommendation="Попробуйте повторить запрос через несколько минут.",
            should_visit_vet=False,
        )
    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        await log_error_to_db("photo_error", str(e)[:500], feature="photo", telegram_id=x_telegram_id)
        send_alert(
            error_type="photo_error",
            error_message=str(e),
            user_telegram_id=x_telegram_id,
            feature="photo",
        )
        if language == "en":
            return PhotoDiagnosisResponse(
                condition="Analysis error",
                confidence=0.0,
                severity="medium",
                description="Could not analyze the photo. Try uploading a different image.",
                recommendation="We recommend showing your pet to a veterinarian for an accurate diagnosis.",
                should_visit_vet=True,
                clinic_link="https://www.google.com/maps/search/veterinary%20clinic%20near%20me",
            )
        return PhotoDiagnosisResponse(
            condition="Ошибка анализа",
            confidence=0.0,
            severity="средняя",
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
    language: str = "ru",
    x_telegram_id: int = Header(...),
):
    """Upload lab results photo/PDF → OCR → LLM interpretation."""
    if not await check_limit(x_telegram_id):
        remaining = await get_remaining(x_telegram_id)
        msg = "Daily limit of 3 requests reached. Try again tomorrow." if language == "en" else "Лимит 3 запроса в день исчерпан. Попробуйте завтра."
        raise HTTPException(
            status_code=429,
            detail={
                "message": msg,
                "remaining": remaining,
            },
        )
    file_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"

    # Convert PDF to image if needed
    if content_type == "application/pdf" or (file.filename and file.filename.lower().endswith(".pdf")):
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(dpi=200)
            file_bytes = pix.tobytes("png")
            content_type = "image/png"
            doc.close()
        except Exception as pdf_err:
            logger.error(f"PDF conversion error: {pdf_err}")

    try:
        result = await interpret_lab_results_image(
            image_bytes=file_bytes,
            pet_species=species,
            content_type=content_type,
            language=language,
        )
        await increment(x_telegram_id, "lab", provider="groq")

        response = LabResultsResponse(
            extracted_text=result.get("extracted_text", ""),
            parsed_values=result.get("parsed_values", {}),
            anomalies=result.get("anomalies", []),
            summary=result.get("summary", "Could not interpret the results." if language == "en" else "Не удалось интерпретировать результаты."),
        )

        # Save diagnosis to DB
        try:
            diag_id = await _save_diagnosis(
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
            response.diagnosis_id = diag_id
        except Exception as save_err:
            logger.error(f"Failed to save lab diagnosis: {save_err}")
            await log_error_to_db("save_diagnosis_error", f"lab: {save_err}", feature="lab", telegram_id=x_telegram_id)

        return response

    except AllProvidersDownError:
        logger.error("All AI providers are down (lab)")
        await log_error_to_db("all_providers_down", "Groq и Claude оба недоступны", feature="lab", telegram_id=x_telegram_id)
        summary = "We're experiencing high demand right now! Please try again in 5-10 minutes." if language == "en" else "Сейчас очень много пользователей! Мы срочно масштабируем серверы. Попробуйте через 5-10 минут."
        return LabResultsResponse(
            extracted_text="",
            parsed_values={},
            anomalies=[],
            summary=summary,
        )
    except Exception as e:
        logger.error(f"Lab results analysis error: {e}")
        await log_error_to_db("lab_error", str(e)[:500], feature="lab", telegram_id=x_telegram_id)
        send_alert(
            error_type="lab_error",
            error_message=str(e),
            user_telegram_id=x_telegram_id,
            feature="lab_results",
        )
        summary = "Analysis error. Try uploading a clearer image." if language == "en" else "Ошибка при анализе. Попробуйте загрузить более чёткое изображение."
        return LabResultsResponse(
            extracted_text=extracted_text,
            parsed_values={},
            anomalies=[],
            summary=summary,
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
            "rating": d.rating,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    return {"items": items, "total": len(items)}


@router.post("/rate/{diagnosis_id}")
async def rate_diagnosis(
    diagnosis_id: int,
    rating: int,
    x_telegram_id: int = Header(...),
):
    """Rate a diagnosis result (1-5 stars)."""
    if rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be 1-5")

    user_id = await _get_user_id(x_telegram_id)
    if user_id is None:
        raise HTTPException(404, "User not found")

    async with async_session() as session:
        diag = (await session.execute(
            select(Diagnosis).where(Diagnosis.id == diagnosis_id, Diagnosis.user_id == user_id)
        )).scalar_one_or_none()

        if diag is None:
            raise HTTPException(404, "Diagnosis not found")

        diag.rating = rating
        await session.commit()

    return {"ok": True, "diagnosis_id": diagnosis_id, "rating": rating}
