"""
Cosmos DB client for VetAI.
Replaces SQLAlchemy + SQLite with Azure Cosmos DB (NoSQL).
Free tier: 1000 RU/s, 25 GB.
"""

import os
import json
import logging
from datetime import datetime, date
from azure.cosmos import CosmosClient, PartitionKey, exceptions

logger = logging.getLogger(__name__)

# Cosmos DB connection
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
COSMOS_DATABASE = "vetai"

_client = None
_database = None
_containers = {}


def get_client():
    global _client
    if _client is None:
        _client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    return _client


def get_database():
    global _database
    if _database is None:
        client = get_client()
        _database = client.create_database_if_not_exists(id=COSMOS_DATABASE)
    return _database


def get_container(name: str):
    if name not in _containers:
        db = get_database()
        partition_key = "/telegram_id" if name == "users" else "/user_id"
        if name == "usage_log":
            partition_key = "/user_id"
        _containers[name] = db.create_container_if_not_exists(
            id=name,
            partition_key=PartitionKey(path=partition_key),
        )
    return _containers[name]


# ============ USER OPERATIONS ============

def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    container = get_container("users")
    query = "SELECT * FROM c WHERE c.telegram_id = @tid"
    params = [{"name": "@tid", "value": telegram_id}]
    items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return items[0] if items else None


def create_user(data: dict) -> dict:
    container = get_container("users")
    data["id"] = str(data["telegram_id"])
    data["created_at"] = datetime.utcnow().isoformat()
    data["login_count"] = 1
    data["last_login"] = datetime.utcnow().isoformat()
    data["pets"] = []
    data["daily_limit_override"] = None
    container.upsert_item(data)
    return data


def update_user(telegram_id: int, updates: dict) -> dict:
    user = get_user_by_telegram_id(telegram_id)
    if user:
        user.update(updates)
        container = get_container("users")
        container.upsert_item(user)
    return user


def add_pet(telegram_id: int, pet: dict) -> dict:
    user = get_user_by_telegram_id(telegram_id)
    if user:
        if "pets" not in user:
            user["pets"] = []
        pet["id"] = len(user["pets"]) + 1
        user["pets"].append(pet)
        container = get_container("users")
        container.upsert_item(user)
    return pet


def get_all_users() -> list:
    container = get_container("users")
    return list(container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True
    ))


# ============ USAGE LOG ============

def log_usage(user_id: str, feature: str, provider: str | None = None):
    container = get_container("usage_log")
    import uuid
    item = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "feature": feature,
        "provider": provider,
        "used_at": datetime.utcnow().isoformat(),
    }
    container.upsert_item(item)


def get_today_usage_count(telegram_id: int) -> int:
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        return 0
    user_id = user["id"]
    container = get_container("usage_log")
    today = date.today().isoformat()
    query = "SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @uid AND STARTSWITH(c.used_at, @today)"
    params = [{"name": "@uid", "value": user_id}, {"name": "@today", "value": today}]
    result = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return result[0] if result else 0


def get_user_limit(telegram_id: int) -> int:
    user = get_user_by_telegram_id(telegram_id)
    if user and user.get("daily_limit_override"):
        return user["daily_limit_override"]
    return 10


# ============ DIAGNOSIS ============

def save_diagnosis(user_id: str, dtype: str, condition: str = None,
                   confidence: float = None, severity: str = None,
                   result_json: dict = None) -> dict:
    container = get_container("diagnoses")
    import uuid
    item = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": dtype,
        "condition": condition,
        "confidence": confidence,
        "severity": severity,
        "result_json": result_json,
        "created_at": datetime.utcnow().isoformat(),
    }
    container.upsert_item(item)
    return item


def get_diagnosis_history(user_id: str, limit: int = 20) -> list:
    container = get_container("diagnoses")
    query = f"SELECT TOP {limit} * FROM c WHERE c.user_id = @uid ORDER BY c.created_at DESC"
    params = [{"name": "@uid", "value": user_id}]
    return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))


# ============ FEEDBACK ============

def save_feedback(user_id: str, message: str):
    container = get_container("feedback")
    import uuid
    item = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": message,
        "created_at": datetime.utcnow().isoformat(),
    }
    container.upsert_item(item)


def get_all_feedback() -> list:
    container = get_container("feedback")
    return list(container.query_items(
        query="SELECT * FROM c ORDER BY c.created_at DESC",
        enable_cross_partition_query=True
    ))


# ============ STATS ============

def get_stats() -> dict:
    users = get_all_users()
    today = date.today().isoformat()

    total_users = len(users)
    new_today = sum(1 for u in users if u.get("created_at", "").startswith(today))

    # Usage stats
    usage_container = get_container("usage_log")
    today_usage = list(usage_container.query_items(
        query="SELECT * FROM c WHERE STARTSWITH(c.used_at, @today)",
        parameters=[{"name": "@today", "value": today}],
        enable_cross_partition_query=True
    ))

    all_usage = list(usage_container.query_items(
        query="SELECT VALUE COUNT(1) FROM c",
        enable_cross_partition_query=True
    ))

    active_today = len(set(u["user_id"] for u in today_usage))

    # By feature
    by_feature = {}
    by_provider = {}
    for u in today_usage:
        f = u.get("feature", "unknown")
        by_feature[f] = by_feature.get(f, 0) + 1
        p = u.get("provider") or "unknown"
        by_provider[p] = by_provider.get(p, 0) + 1

    # Diagnoses count
    diag_container = get_container("diagnoses")
    diag_count = list(diag_container.query_items(
        query="SELECT VALUE COUNT(1) FROM c",
        enable_cross_partition_query=True
    ))

    return {
        "users": {"total": total_users, "new_today": new_today, "active_today": active_today},
        "requests": {
            "today": len(today_usage),
            "total": all_usage[0] if all_usage else 0,
            "by_feature_today": by_feature,
            "by_provider_today": by_provider,
        },
        "diagnoses_total": diag_count[0] if diag_count else 0,
    }
