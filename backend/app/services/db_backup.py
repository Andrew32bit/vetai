"""
SQLite backup to Azure Cosmos DB (Blob attachment).
Saves vetai.db as base64 blob so it survives container restarts.
Fallback: HuggingFace Hub if Cosmos not configured.
"""

import os
import base64
import asyncio
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

DB_PATH = "./vetai.db"
BACKUP_INTERVAL = 300  # 5 minutes


async def restore_db():
    """Download DB from Cosmos DB or HF Hub on startup."""
    settings = get_settings()

    # Try Cosmos DB first
    if os.environ.get("COSMOS_ENDPOINT") and os.environ.get("COSMOS_KEY"):
        try:
            from azure.cosmos import CosmosClient
            client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
            db = client.create_database_if_not_exists("vetai")
            backups = db.create_container_if_not_exists(
                id="backups",
                partition_key={"paths": ["/id"], "kind": "Hash"},
            )
            try:
                item = backups.read_item(item="sqlite_backup", partition_key="sqlite_backup")
                db_bytes = base64.b64decode(item["data"])
                with open(DB_PATH, "wb") as f:
                    f.write(db_bytes)
                logger.info(f"DB restored from Cosmos DB ({len(db_bytes)} bytes)")
                return
            except Exception as e:
                logger.info(f"No Cosmos backup found: {e}")
        except Exception as e:
            logger.error(f"Cosmos restore failed: {e}")

    # Fallback: HuggingFace Hub
    try:
        if settings.HF_API_TOKEN:
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(
                repo_id="kombatDrew/vetai-data",
                filename="vetai.db",
                repo_type="dataset",
                token=settings.HF_API_TOKEN,
                local_dir=".",
            )
            logger.info(f"DB restored from HF Hub: {path}")
        else:
            logger.info("No backup source configured, starting fresh")
    except Exception as e:
        logger.info(f"No HF backup found, starting fresh: {e}")


async def backup_db():
    """Upload DB to Cosmos DB."""
    if not os.path.exists(DB_PATH):
        return

    # Try Cosmos DB
    if os.environ.get("COSMOS_ENDPOINT") and os.environ.get("COSMOS_KEY"):
        try:
            with open(DB_PATH, "rb") as f:
                db_bytes = f.read()

            from azure.cosmos import CosmosClient
            client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
            db = client.create_database_if_not_exists("vetai")
            backups = db.create_container_if_not_exists(
                id="backups",
                partition_key={"paths": ["/id"], "kind": "Hash"},
            )
            backups.upsert_item({
                "id": "sqlite_backup",
                "data": base64.b64encode(db_bytes).decode(),
                "size": len(db_bytes),
            })
            logger.info(f"DB backed up to Cosmos DB ({len(db_bytes)} bytes)")
            return
        except Exception as e:
            logger.error(f"Cosmos backup failed: {e}")

    # Fallback: HuggingFace
    try:
        settings = get_settings()
        if settings.HF_API_TOKEN:
            from huggingface_hub import HfApi
            api = HfApi(token=settings.HF_API_TOKEN)
            api.upload_file(
                path_or_fileobj=DB_PATH,
                path_in_repo="vetai.db",
                repo_id="kombatDrew/vetai-data",
                repo_type="dataset",
            )
            logger.info("DB backed up to HF Hub")
    except Exception as e:
        logger.error(f"HF backup failed: {e}")


async def periodic_backup():
    """Run backup every BACKUP_INTERVAL seconds."""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL)
        await backup_db()
