"""
User management: auth via Telegram initData, registration, pet profiles, subscriptions.
"""

from datetime import datetime
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.database import async_session, User, Pet
from app.services.usage_limiter import get_remaining, DAILY_LIMIT

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

            usage_today = DAILY_LIMIT - await get_remaining(data.telegram_id)

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
                "usage_today": usage_today,
                "usage_limit": DAILY_LIMIT,
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

        usage_today = DAILY_LIMIT - await get_remaining(x_telegram_id)

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
            "usage_today": usage_today,
            "usage_limit": DAILY_LIMIT,
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
