"""
User management: registration via Telegram initData, pet profiles, subscriptions.
"""

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# --- Schemas ---

class PetCreate(BaseModel):
    name: str
    species: str  # "cat" | "dog"
    breed: Optional[str] = None
    age_months: Optional[int] = None
    weight_kg: Optional[float] = None


class UserCreate(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    pet: PetCreate


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    subscription_tier: str  # "free" | "monthly" | "annual"
    pets: list


# --- Endpoints ---

@router.post("/register", response_model=dict)
async def register_user(data: UserCreate):
    """
    Register user from Telegram Mini App onboarding.
    Validates Telegram initData hash for auth.
    """
    # TODO: validate Telegram initData
    # TODO: create user + pet in DB
    return {
        "ok": True,
        "user_id": 1,
        "message": "Добро пожаловать в VetAI!",
    }


@router.get("/me", response_model=dict)
async def get_current_user(x_telegram_id: int = Header(...)):
    """Get current user profile with pets."""
    # TODO: fetch from DB by telegram_id
    return {
        "id": 1,
        "telegram_id": x_telegram_id,
        "first_name": "User",
        "subscription_tier": "free",
        "pets": [],
    }


@router.post("/subscribe")
async def subscribe(tier: str, x_telegram_id: int = Header(...)):
    """
    Upgrade subscription.
    tier: "monthly" (99₽) | "annual" (1000₽)
    Payment via Telegram Stars or YooKassa.
    """
    # TODO: integrate Telegram Payments / YooKassa
    return {"ok": True, "tier": tier}
