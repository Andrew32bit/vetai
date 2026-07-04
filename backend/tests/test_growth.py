"""
Regression tests for the growth features (analytics, referral loop, streak).

Runs with pytest OR standalone:  python tests/test_growth.py
Uses an isolated temp SQLite DB so it never touches the production vetai.db.
"""

import os
import asyncio
import tempfile

# Must set env BEFORE importing app modules (config caches settings on first use).
_TMP_DB = os.path.join(tempfile.gettempdir(), "vetai_test_growth.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DB}"
os.environ["ADMIN_KEY"] = "test-key"
os.environ.setdefault("DEBUG", "false")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.database import init_db
from app.routers import analytics, user
from app.services.growth import parse_referrer


def _make_client():
    app = FastAPI()
    app.include_router(user.router, prefix="/api/v1/users")
    app.include_router(analytics.router, prefix="/api/v1/analytics")
    asyncio.get_event_loop().run_until_complete(init_db())
    return TestClient(app)


def test_parse_referrer():
    assert parse_referrer(12345, None) == 12345
    assert parse_referrer(None, "ref_777") == 777
    assert parse_referrer(None, "ref888") == 888
    assert parse_referrer(None, "garbage") is None
    assert parse_referrer(None, None) is None


def test_referral_and_analytics_flow():
    c = _make_client()

    # Referrer signs up
    r = c.post("/api/v1/users/auth", json={"telegram_id": 100, "first_name": "Ref"})
    assert r.status_code == 200 and r.json()["is_new"] is True

    # Invitee arrives via referral deep-link
    r = c.post("/api/v1/users/auth",
               json={"telegram_id": 200, "first_name": "Inv", "start_param": "ref_100"})
    assert r.json()["referred"] is True

    # Duplicate signup must NOT double-credit
    r = c.post("/api/v1/users/auth",
               json={"telegram_id": 200, "first_name": "Inv", "start_param": "ref_100"})
    assert r.json()["is_new"] is False

    # Referrer got the reward: +5 daily requests, count = 1
    info = c.get("/api/v1/users/referral-info", headers={"x-telegram-id": "100"}).json()
    assert info["referral_count"] == 1
    assert info["daily_limit"] == 15  # 10 base + 5 bonus

    # Analytics ingest + allowlist
    for ev in ["app_open", "onboarding_complete", "ai_start", "ai_success"]:
        assert c.post("/api/v1/analytics/events",
                      json={"event": ev, "telegram_id": 200, "session_id": "s1"}).json()["ok"]
    assert c.post("/api/v1/analytics/events", json={"event": "__bogus__"}).json()["stored"] is False

    # Public trust stats (no auth, no PII)
    ps = c.get("/api/v1/analytics/public-stats").json()
    assert ps["users"] >= 2 and "checks" in ps

    # Admin funnel is auth-gated and returns data
    assert c.get("/api/v1/analytics/funnel").status_code == 422           # header required
    assert c.get("/api/v1/analytics/funnel",
                 headers={"admin-key": "wrong"}).status_code == 403       # bad key
    f = c.get("/api/v1/analytics/funnel", headers={"admin-key": "test-key"}).json()
    assert f["users_total"] >= 2
    assert f["referrals"]["total"] == 1
    assert f["events"].get("app_open", 0) >= 1


if __name__ == "__main__":
    test_parse_referrer()
    print("test_parse_referrer: OK")
    test_referral_and_analytics_flow()
    print("test_referral_and_analytics_flow: OK")
    print("ALL GROWTH TESTS PASSED")
