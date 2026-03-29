#!/usr/bin/env python3
"""
Download vetai.db from HuggingFace Hub to local backups/ directory.
Usage: HF_TOKEN=hf_xxx python scripts/backup_local.py
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "kombatDrew/vetai-data"
TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_TOKEN")
BACKUP_DIR = Path(__file__).parent.parent / "backups"

if not TOKEN:
    print("Error: set HF_TOKEN environment variable")
    print("Usage: HF_TOKEN=hf_xxx python scripts/backup_local.py")
    exit(1)

BACKUP_DIR.mkdir(exist_ok=True)

path = hf_hub_download(
    repo_id=REPO_ID,
    filename="vetai.db",
    repo_type="dataset",
    token=TOKEN,
    local_dir=str(BACKUP_DIR),
)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
timestamped = BACKUP_DIR / f"vetai_{ts}.db"
shutil.copy2(path, timestamped)

print(f"Latest:      {BACKUP_DIR}/vetai.db")
print(f"Timestamped: {timestamped}")

# Show DB stats
import sqlite3
conn = sqlite3.connect(str(BACKUP_DIR / "vetai.db"))
cur = conn.cursor()
users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
diagnoses = cur.execute("SELECT COUNT(*) FROM diagnoses").fetchone()[0]
usage = cur.execute("SELECT COUNT(*) FROM usage_log").fetchone()[0]
print(f"\nDB stats: {users} users, {diagnoses} diagnoses, {usage} usage logs")
conn.close()
