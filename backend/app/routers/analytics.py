"""
Product analytics: event ingestion + admin funnel/retention dashboard.

Events are the foundation for DAU optimization — you cannot improve activation,
retention or virality without measuring the funnel. Frontend posts events to
POST /events; admins read the funnel via GET /funnel (admin-key header).
"""

import json
import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from app.config import verify_admin_key
from app.models.database import async_session, AnalyticsEvent, User, UsageLog, Referral

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed event names — keeps the table clean and prevents unbounded cardinality.
ALLOWED_EVENTS = {
    "app_open",
    "onboarding_start",
    "onboarding_complete",
    "ai_start",
    "ai_success",
    "ai_failure",
    "share_click",
    "share_result_click",
    "invite_click",
    "invite_copy",
    "referral_landed",
    "paywall_view",
    "purchase",
    "notification_open",
    "streak_view",
}


class EventIn(BaseModel):
    event: str
    telegram_id: int | None = None
    session_id: str | None = None
    props: dict | None = None


@router.post("/events")
async def track_event(ev: EventIn):
    """Ingest a single product-analytics event. Fire-and-forget from the client."""
    if ev.event not in ALLOWED_EVENTS:
        # Unknown event — accept but do not store, to avoid cardinality blowups.
        return {"ok": True, "stored": False}

    props_str = None
    if ev.props:
        try:
            props_str = json.dumps(ev.props, ensure_ascii=False)[:1000]
        except Exception:
            props_str = None

    try:
        async with async_session() as session:
            session.add(AnalyticsEvent(
                telegram_id=ev.telegram_id,
                event=ev.event,
                props=props_str,
                session_id=(ev.session_id or "")[:40] or None,
            ))
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to store event {ev.event}: {e}")
        return {"ok": False}

    return {"ok": True, "stored": True}


@router.get("/public-stats")
async def public_stats():
    """Aggregate, non-sensitive counts for social-proof/trust UI (no PII)."""
    async with async_session() as session:
        from app.models.database import Diagnosis
        checks = (await session.execute(select(func.count(Diagnosis.id)))).scalar() or 0
        users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    # Round users down to a friendlier band; expose exact checks (grows engagement).
    return {"checks": checks, "users": users}


@router.get("/funnel")
async def funnel(admin_key: str = Header(...), days: int = 7):
    """Activation funnel, DAU/WAU, retention and referral stats for admins."""
    if not verify_admin_key(admin_key):
        raise HTTPException(status_code=403, detail="Forbidden")

    today = date.today()
    today_iso = today.isoformat()
    week_ago = (today - timedelta(days=7)).isoformat()

    async with async_session() as session:
        # --- DAU / WAU (from real usage, the strongest activity signal) ---
        dau = (await session.execute(
            select(func.count(func.distinct(UsageLog.user_id)))
            .where(func.date(UsageLog.used_at) == today_iso)
        )).scalar() or 0
        wau = (await session.execute(
            select(func.count(func.distinct(UsageLog.user_id)))
            .where(func.date(UsageLog.used_at) >= week_ago)
        )).scalar() or 0

        users_total = (await session.execute(select(func.count(User.id)))).scalar() or 0
        new_today = (await session.execute(
            select(func.count(User.id)).where(func.date(User.created_at) == today_iso)
        )).scalar() or 0

        # --- Activation: of users created in the window, how many ever made a request ---
        window_start = (today - timedelta(days=days)).isoformat()
        cohort = (await session.execute(
            select(func.count(User.id)).where(func.date(User.created_at) >= window_start)
        )).scalar() or 0
        activated = (await session.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User).join(UsageLog, UsageLog.user_id == User.id)
            .where(func.date(User.created_at) >= window_start)
        )).scalar() or 0
        activation_rate = round(activated / cohort, 3) if cohort else 0.0

        # --- Returning users today (active today AND registered before today) ---
        returning = (await session.execute(
            select(func.count(func.distinct(UsageLog.user_id)))
            .select_from(UsageLog).join(User, UsageLog.user_id == User.id)
            .where(
                func.date(UsageLog.used_at) == today_iso,
                func.date(User.created_at) < today_iso,
            )
        )).scalar() or 0

        # --- Event funnel over the window (from analytics_event) ---
        ev_rows = (await session.execute(
            select(AnalyticsEvent.event, func.count(AnalyticsEvent.id))
            .where(func.date(AnalyticsEvent.created_at) >= window_start)
            .group_by(AnalyticsEvent.event)
        )).all()
        events = {name: cnt for name, cnt in ev_rows}

        # --- Referrals ---
        referrals_total = (await session.execute(select(func.count(Referral.id)))).scalar() or 0
        top_ref_rows = (await session.execute(
            select(Referral.referrer_telegram_id, func.count(Referral.id).label("c"))
            .group_by(Referral.referrer_telegram_id)
            .order_by(func.count(Referral.id).desc())
            .limit(5)
        )).all()
        top_referrers = [{"telegram_id": tid, "invites": c} for tid, c in top_ref_rows]

        # Broadcast delivery breakdown (from notification_sent events)
        delivered = (await session.execute(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event == "notification_sent",
                AnalyticsEvent.props.like('%"ok": true%'),
            )
        )).scalar() or 0
        notif_failed = (await session.execute(
            select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event == "notification_sent",
                AnalyticsEvent.props.like('%"ok": false%'),
            )
        )).scalar() or 0

    return {
        "window_days": days,
        "users_total": users_total,
        "new_users_today": new_today,
        "dau": dau,
        "wau": wau,
        "dau_wau_ratio": round(dau / wau, 3) if wau else 0.0,  # stickiness
        "returning_today": returning,
        "activation": {
            "cohort": cohort,
            "activated": activated,
            "rate": activation_rate,
        },
        "events": events,
        "referrals": {
            "total": referrals_total,
            "top_referrers": top_referrers,
        },
        "broadcast": {
            "delivered": delivered,
            "failed": notif_failed,
        },
    }
