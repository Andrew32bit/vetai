"""
Growth mechanics: referral rewards and daily-usage streaks.

Referral reward model: each successful referral grants the referrer +REFERRAL_BONUS
requests to their daily limit (capped at MAX_DAILY_LIMIT). This turns Telegram's
native sharing into a viral acquisition loop without any paid spend.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.models.database import async_session, User, Referral

logger = logging.getLogger(__name__)

REFERRAL_BONUS = 5          # extra daily requests per successful referral
MAX_DAILY_LIMIT = 50        # cap on daily_limit_override from referrals
BASE_DAILY_LIMIT = 10       # keep in sync with usage_limiter.DAILY_LIMIT


def parse_referrer(ref: int | None, start_param: str | None) -> int | None:
    """Extract a referrer telegram_id from an explicit `ref` or a Telegram
    start_param like `ref_12345` / `ref12345`. Returns None if absent/invalid."""
    if ref:
        try:
            return int(ref)
        except (TypeError, ValueError):
            pass
    if start_param:
        s = str(start_param).strip().lower()
        if s.startswith("ref_"):
            s = s[4:]
        elif s.startswith("ref"):
            s = s[3:]
        else:
            return None
        try:
            return int(s)
        except (TypeError, ValueError):
            return None
    return None


async def apply_referral(invitee_telegram_id: int, referrer_telegram_id: int) -> bool:
    """Credit a referrer for inviting `invitee`. Idempotent per invitee.

    Returns True if a NEW referral was recorded and reward granted.
    """
    if not referrer_telegram_id or referrer_telegram_id == invitee_telegram_id:
        return False

    async with async_session() as session:
        # Idempotency: one reward per invited user, ever.
        existing = await session.execute(
            select(Referral).where(Referral.invitee_telegram_id == invitee_telegram_id)
        )
        if existing.scalar_one_or_none() is not None:
            return False

        referrer = (await session.execute(
            select(User).where(User.telegram_id == referrer_telegram_id)
        )).scalar_one_or_none()
        if referrer is None:
            return False  # unknown referrer — ignore silently

        # Record referral + mark invitee + reward referrer.
        session.add(Referral(
            referrer_telegram_id=referrer_telegram_id,
            invitee_telegram_id=invitee_telegram_id,
        ))

        invitee = (await session.execute(
            select(User).where(User.telegram_id == invitee_telegram_id)
        )).scalar_one_or_none()
        if invitee is not None and invitee.referred_by is None:
            invitee.referred_by = referrer_telegram_id

        referrer.referral_count = (referrer.referral_count or 0) + 1
        current_limit = referrer.daily_limit_override or BASE_DAILY_LIMIT
        referrer.daily_limit_override = min(current_limit + REFERRAL_BONUS, MAX_DAILY_LIMIT)

        await session.commit()
        logger.info(
            "Referral: %s invited %s (referrer now %s invites, limit %s)",
            referrer_telegram_id, invitee_telegram_id,
            referrer.referral_count, referrer.daily_limit_override,
        )
        return True


async def update_streak(telegram_id: int) -> int:
    """Update a user's daily-usage streak. Call on each successful request.

    Streak increments once per calendar day of activity; resets if a day is
    skipped. Returns the current streak length (0 if user not found).
    """
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if user is None:
            return 0

        today = date.today()
        last = user.last_active_date
        if last == today.isoformat():
            return user.streak_count or 0  # already counted today

        if last == (today - timedelta(days=1)).isoformat():
            user.streak_count = (user.streak_count or 0) + 1  # consecutive day
        else:
            user.streak_count = 1  # first day or streak broken

        user.last_active_date = today.isoformat()
        await session.commit()
        return user.streak_count


async def get_referral_stats(telegram_id: int) -> dict:
    """Referral count + current daily limit for display in the invite UI."""
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if user is None:
            return {"referral_count": 0, "daily_limit": BASE_DAILY_LIMIT, "bonus_per_invite": REFERRAL_BONUS}
        return {
            "referral_count": user.referral_count or 0,
            "daily_limit": user.daily_limit_override or BASE_DAILY_LIMIT,
            "bonus_per_invite": REFERRAL_BONUS,
        }
