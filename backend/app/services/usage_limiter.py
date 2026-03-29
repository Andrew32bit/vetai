"""
Usage limiter for beta free tier.
Tracks daily usage per user in SQLite via async SQLAlchemy.
Beta limit: 3 requests/day total (all features combined).
"""

from datetime import date, datetime
from sqlalchemy import select, func

from app.models.database import async_session, UsageLog, User

DAILY_LIMIT = 10


async def _get_today_count(telegram_id: int) -> int:
    """Get total usage count for today for a given telegram_id."""
    async with async_session() as session:
        today = date.today().isoformat()
        result = await session.execute(
            select(func.count(UsageLog.id))
            .join(User, UsageLog.user_id == User.id)
            .where(
                User.telegram_id == telegram_id,
                func.date(UsageLog.used_at) == today,
            )
        )
        return result.scalar() or 0


async def _get_user_limit(telegram_id: int) -> int:
    """Get effective daily limit for a user (override or default)."""
    async with async_session() as session:
        result = await session.execute(
            select(User.daily_limit_override).where(User.telegram_id == telegram_id)
        )
        override = result.scalar_one_or_none()
        return override if override is not None else DAILY_LIMIT


async def check_limit(telegram_id: int) -> bool:
    """Return True if the user can still make requests today."""
    count = await _get_today_count(telegram_id)
    limit = await _get_user_limit(telegram_id)
    return count < limit


async def increment(telegram_id: int, feature: str) -> None:
    """Record a usage event for the user."""
    async with async_session() as session:
        # Find user_id by telegram_id
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        user_id = result.scalar()
        if user_id is None:
            return
        log = UsageLog(user_id=user_id, feature=feature, used_at=datetime.utcnow())
        session.add(log)
        await session.commit()


async def get_remaining(telegram_id: int) -> int:
    """Return how many requests remain today."""
    count = await _get_today_count(telegram_id)
    limit = await _get_user_limit(telegram_id)
    return max(0, limit - count)
