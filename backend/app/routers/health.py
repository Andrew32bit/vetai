from fastapi import APIRouter, Header, HTTPException

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "vetai"}


@router.post("/admin/backup")
async def trigger_backup(admin_key: str = Header(...)):
    if admin_key != "vetai-admin-2026":
        raise HTTPException(status_code=403, detail="Forbidden")
    from app.services.db_backup import backup_db
    await backup_db()
    return {"ok": True, "message": "Backup completed"}
