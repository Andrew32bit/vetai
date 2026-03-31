"""
User management: auth via Telegram initData, registration, pet profiles, subscriptions.
"""

from datetime import datetime, date
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.database import async_session, User, Pet, UsageLog, Diagnosis
from app.services.usage_limiter import get_usage_info

router = APIRouter()


# --- Schemas ---

class PetData(BaseModel):
    name: str
    species: str  # "cat" | "dog"
    breed: Optional[str] = None


class AuthRequest(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = "ru"
    is_premium: Optional[bool] = False
    platform: Optional[str] = None


class RegisterRequest(BaseModel):
    telegram_id: int
    pet: PetData
    city: Optional[str] = None


# --- Endpoints ---

@router.post("/auth", response_model=dict)
async def auth_user(data: AuthRequest):
    """
    Authenticate user from Telegram Mini App.
    Creates new user or updates existing one.
    """
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.pets))
            .where(User.telegram_id == data.telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            # Existing user — update fields
            user.last_login = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            if data.username is not None:
                user.username = data.username
            if data.platform is not None:
                user.platform = data.platform
            await session.commit()
            await session.refresh(user)

            usage = await get_usage_info(data.telegram_id)

            pets_list = [
                {"id": p.id, "name": p.name, "species": p.species, "breed": p.breed}
                for p in user.pets
            ]

            return {
                "is_new": False,
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "first_name": user.first_name,
                    "subscription_tier": user.subscription_tier,
                    "city": user.city,
                    "pets": pets_list,
                },
                "usage_today": usage["usage_today"],
                "usage_limit": usage["usage_limit"],
            }
        else:
            # New user
            new_user = User(
                telegram_id=data.telegram_id,
                first_name=data.first_name,
                last_name=data.last_name,
                username=data.username,
                language_code=data.language_code or "ru",
                is_premium=data.is_premium or False,
                platform=data.platform,
                login_count=1,
                last_login=datetime.utcnow(),
                subscription_tier="beta",
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            return {
                "is_new": True,
                "user_id": new_user.id,
            }


@router.post("/register", response_model=dict)
async def register_user(data: RegisterRequest):
    """
    Complete onboarding: add pet + city for existing user.
    Called after /auth returns is_new=true.
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == data.telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found. Call /auth first.")

        # Update city
        if data.city:
            user.city = data.city

        # Create pet
        pet = Pet(
            user_id=user.id,
            name=data.pet.name,
            species=data.pet.species,
            breed=data.pet.breed,
        )
        session.add(pet)
        await session.commit()

        return {
            "ok": True,
            "user_id": user.id,
            "message": "Добро пожаловать в VetAI!",
        }


@router.get("/me", response_model=dict)
async def get_current_user(x_telegram_id: int = Header(...)):
    """Get current user profile with pets and usage info."""
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.pets))
            .where(User.telegram_id == x_telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        usage = await get_usage_info(x_telegram_id)

        pets_list = [
            {"id": p.id, "name": p.name, "species": p.species, "breed": p.breed}
            for p in user.pets
        ]

        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "subscription_tier": user.subscription_tier,
            "city": user.city,
            "pets": pets_list,
            "usage_today": usage["usage_today"],
            "usage_limit": usage["usage_limit"],
        }


@router.post("/subscribe")
async def subscribe(tier: str, x_telegram_id: int = Header(...)):
    """
    Upgrade subscription.
    tier: "monthly" (99 RUB) | "annual" (1000 RUB)
    Payment via Telegram Stars or YooKassa.
    """
    # TODO: integrate Telegram Payments / YooKassa
    return {"ok": True, "tier": tier}


# --- Admin Endpoints ---

@router.post("/admin/set-limit")
async def set_user_limit(telegram_id: int, daily_limit: int, admin_key: str = Header(...)):
    """Set a custom daily limit override for a user."""
    if admin_key != "vetai-admin-2026":
        raise HTTPException(status_code=403, detail="Forbidden")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        user.daily_limit_override = daily_limit
        await session.commit()

    return {"ok": True, "telegram_id": telegram_id, "daily_limit": daily_limit}


@router.get("/admin/users")
async def list_users(admin_key: str = Header(...)):
    """List all users with stats (admin only)."""
    if admin_key != "vetai-admin-2026":
        raise HTTPException(status_code=403, detail="Forbidden")

    today = date.today().isoformat()

    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.pets))
        )
        users = result.scalars().all()

        users_list = []
        for u in users:
            # Count today's usage
            usage_result = await session.execute(
                select(func.count(UsageLog.id)).where(
                    UsageLog.user_id == u.id,
                    func.date(UsageLog.used_at) == today,
                )
            )
            usage_today = usage_result.scalar() or 0

            users_list.append({
                "id": u.id,
                "telegram_id": u.telegram_id,
                "first_name": u.first_name,
                "username": u.username,
                "city": u.city,
                "login_count": u.login_count,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "daily_limit_override": u.daily_limit_override,
                "pets_count": len(u.pets),
                "usage_today": usage_today,
            })

    return {"users": users_list, "total": len(users_list)}


# --- Feedback ---

class FeedbackRequest(BaseModel):
    message: str


@router.post("/feedback")
async def submit_feedback(
    data: FeedbackRequest,
    x_telegram_id: int = Header(...),
):
    """Save user feedback."""
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(User.telegram_id == x_telegram_id)
        )
        user_id = result.scalar_one_or_none()
        if user_id is None:
            raise HTTPException(404, "User not found")

        from app.models.database import Feedback
        fb = Feedback(user_id=user_id, message=data.message)
        session.add(fb)
        await session.commit()

    return {"ok": True}


@router.get("/admin/feedback")
async def list_feedback(admin_key: str = Header(...)):
    """List all feedback."""
    if admin_key != "vetai-admin-2026":
        raise HTTPException(403, "Forbidden")

    from app.models.database import Feedback
    async with async_session() as session:
        result = await session.execute(
            select(Feedback, User.first_name, User.username)
            .join(User, Feedback.user_id == User.id)
            .order_by(Feedback.created_at.desc())
        )
        rows = result.all()

    return {
        "feedback": [
            {
                "id": fb.id,
                "user": f"{name} (@{uname})" if uname else name,
                "message": fb.message,
                "created_at": fb.created_at.isoformat(),
            }
            for fb, name, uname in rows
        ],
        "total": len(rows),
    }


@router.get("/admin/stats")
async def get_stats(admin_key: str = Header(...)):
    """Сводная аналитика: пользователи, запросы, провайдеры, фичи."""
    if admin_key != "vetai-admin-2026":
        raise HTTPException(403, "Forbidden")

    today = date.today().isoformat()

    async with async_session() as session:
        # Всего пользователей
        total_users = (await session.execute(
            select(func.count(User.id))
        )).scalar() or 0

        # Новые пользователи сегодня
        new_today = (await session.execute(
            select(func.count(User.id)).where(func.date(User.created_at) == today)
        )).scalar() or 0

        # Активные сегодня (сделали хотя бы 1 запрос)
        active_today = (await session.execute(
            select(func.count(func.distinct(UsageLog.user_id)))
            .where(func.date(UsageLog.used_at) == today)
        )).scalar() or 0

        # Запросы сегодня
        requests_today = (await session.execute(
            select(func.count(UsageLog.id)).where(func.date(UsageLog.used_at) == today)
        )).scalar() or 0

        # Запросы всего
        requests_total = (await session.execute(
            select(func.count(UsageLog.id))
        )).scalar() or 0

        # По фичам сегодня
        features_today_rows = (await session.execute(
            select(UsageLog.feature, func.count(UsageLog.id))
            .where(func.date(UsageLog.used_at) == today)
            .group_by(UsageLog.feature)
        )).all()
        features_today = {f: c for f, c in features_today_rows}

        # По провайдерам сегодня
        providers_today_rows = (await session.execute(
            select(UsageLog.provider, func.count(UsageLog.id))
            .where(func.date(UsageLog.used_at) == today)
            .group_by(UsageLog.provider)
        )).all()
        providers_today = {(p or "unknown"): c for p, c in providers_today_rows}

        # По провайдерам всего
        providers_total_rows = (await session.execute(
            select(UsageLog.provider, func.count(UsageLog.id))
            .group_by(UsageLog.provider)
        )).all()
        providers_total = {(p or "unknown"): c for p, c in providers_total_rows}

        # Запросы за последние 7 дней (по дням)
        from datetime import timedelta
        week_ago = (date.today() - timedelta(days=6)).isoformat()
        daily_rows = (await session.execute(
            select(func.date(UsageLog.used_at), func.count(UsageLog.id))
            .where(func.date(UsageLog.used_at) >= week_ago)
            .group_by(func.date(UsageLog.used_at))
            .order_by(func.date(UsageLog.used_at))
        )).all()
        daily = {str(d): c for d, c in daily_rows}

        # Диагнозы всего
        diagnoses_total = (await session.execute(
            select(func.count(Diagnosis.id))
        )).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "new_today": new_today,
            "active_today": active_today,
        },
        "requests": {
            "today": requests_today,
            "total": requests_total,
            "by_feature_today": features_today,
            "by_provider_today": providers_today,
            "by_provider_total": providers_total,
            "daily_7d": daily,
        },
        "diagnoses_total": diagnoses_total,
    }
