"""
SQLite backup to HuggingFace Hub.
Saves vetai.db to a HF dataset repo so it survives container restarts.
"""

import os
import asyncio
import logging
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)

HF_BACKUP_REPO = "kombatDrew/vetai-data"
DB_PATH = "./vetai.db"
BACKUP_INTERVAL = 300  # 5 minutes


async def _get_api():
    from huggingface_hub import HfApi
    settings = get_settings()
    return HfApi(token=settings.HF_API_TOKEN)


async def restore_db():
    """Download DB from HF Hub on startup."""
    try:
        api = await _get_api()

        # Ensure repo exists
        try:
            api.create_repo(repo_id=HF_BACKUP_REPO, repo_type="dataset", private=True, exist_ok=True)
        except Exception:
            pass

        # Try to download
        try:
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(
                repo_id=HF_BACKUP_REPO,
                filename="vetai.db",
                repo_type="dataset",
                token=get_settings().HF_API_TOKEN,
                local_dir=".",
            )
            logger.info(f"DB restored from HF Hub: {path}")
        except Exception as e:
            logger.info(f"No backup found, starting fresh: {e}")

    except Exception as e:
        logger.error(f"DB restore failed: {e}")


async def backup_db():
    """Upload DB to HF Hub."""
    if not os.path.exists(DB_PATH):
        return

    try:
        api = await _get_api()
        api.upload_file(
            path_or_fileobj=DB_PATH,
            path_in_repo="vetai.db",
            repo_id=HF_BACKUP_REPO,
            repo_type="dataset",
        )
        logger.info("DB backed up to HF Hub")
    except Exception as e:
        logger.error(f"DB backup failed: {e}")


async def periodic_backup():
    """Run backup every BACKUP_INTERVAL seconds."""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL)
        await backup_db()
