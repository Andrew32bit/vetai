"""
In-memory usage limiter for beta free tier.
Tracks daily usage per telegram_id with automatic daily reset.
"""

from datetime import date
from typing import Dict, Tuple

# Daily limits per feature
DAILY_LIMITS = {
    "photo": 5,
    "chat": 20,
    "lab": 3,
}

# In-memory storage: {(telegram_id, feature): {"date": date, "count": int}}
_usage: Dict[Tuple[int, str], dict] = {}


def _get_entry(telegram_id: int, feature: str) -> dict:
    """Get or create usage entry, resetting if it's a new day."""
    key = (telegram_id, feature)
    today = date.today()
    entry = _usage.get(key)
    if entry is None or entry["date"] != today:
        entry = {"date": today, "count": 0}
        _usage[key] = entry
    return entry


def check_limit(telegram_id: int, feature: str) -> bool:
    """Return True if the user can still use this feature today."""
    entry = _get_entry(telegram_id, feature)
    limit = DAILY_LIMITS.get(feature, 0)
    return entry["count"] < limit


def increment(telegram_id: int, feature: str) -> None:
    """Increment the usage counter for a feature."""
    entry = _get_entry(telegram_id, feature)
    entry["count"] += 1


def get_remaining(telegram_id: int, feature: str) -> int:
    """Return how many uses remain today for this feature."""
    entry = _get_entry(telegram_id, feature)
    limit = DAILY_LIMITS.get(feature, 0)
    return max(0, limit - entry["count"])
