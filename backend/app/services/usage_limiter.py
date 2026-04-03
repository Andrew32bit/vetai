"""
Usage limiter for beta free tier.
Tracks daily usage per user in SQLite via async SQLAlchemy.
Beta limit: 3 requests/day total (all features combined).
"""

from datetime import date, datetime
from sqlalchemy import select, func

from app.models.database import async_session, UsageLog, User
from app.services.alerting import send_alert

DAILY_LIMIT = 10

# Traffic alert thresholds (requests/day)
_traffic_alerts_sent: set[int] = set()
TRAFFIC_THRESHOLDS = [30, 60, 100, 200, 500]


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


async def increment(telegram_id: int, feature: str, provider: str | None = None) -> None:
    """Record a usage event for the user."""
    async with async_session() as session:
        # Find user_id by telegram_id
        result = await session.execute(
            select(User.id).where(User.telegram_id == telegram_id)
        )
        user_id = result.scalar()
        if user_id is None:
            return
        log = UsageLog(user_id=user_id, feature=feature, provider=provider, used_at=datetime.utcnow())
        session.add(log)
        await session.commit()

        # Check daily traffic thresholds
        today = date.today().isoformat()
        total_today = (await session.execute(
            select(func.count(UsageLog.id)).where(func.date(UsageLog.used_at) == today)
        )).scalar() or 0

        active_users = (await session.execute(
            select(func.count(func.distinct(UsageLog.user_id))).where(func.date(UsageLog.used_at) == today)
        )).scalar() or 0

        for threshold in TRAFFIC_THRESHOLDS:
            if total_today >= threshold and threshold not in _traffic_alerts_sent:
                _traffic_alerts_sent.add(threshold)
                action = ""
                if threshold == 30:
                    action = "\n⚡ Рекомендация: переключить на Azure B1"
                elif threshold == 60:
                    action = "\n🔴 СРОЧНО: переключить на Azure B1 ($13/мес)"
                elif threshold >= 100:
                    action = "\n🚨 КРИТИЧНО: нужен PostgreSQL + B1/B2"
                send_alert(
                    error_type="traffic_warning",
                    error_message=f"Запросов сегодня: {total_today}, активных юзеров: {active_users}{action}",
                    feature="traffic",
                )


async def get_remaining(telegram_id: int) -> int:
    """Return how many requests remain today."""
    count = await _get_today_count(telegram_id)
    limit = await _get_user_limit(telegram_id)
    return max(0, limit - count)


async def get_usage_info(telegram_id: int) -> dict:
    """Return usage_today and usage_limit for display."""
    count = await _get_today_count(telegram_id)
    limit = await _get_user_limit(telegram_id)
    return {"usage_today": count, "usage_limit": limit}
