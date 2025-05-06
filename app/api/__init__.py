from fastapi import APIRouter

from app.core.database import SessionLocal
from app.models import IngestLog

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get("/admin/ingest-log")
async def ingest_log(page: int = 1, page_size: int = 100):
    session = SessionLocal()
    try:
        q = session.query(IngestLog).order_by(IngestLog.timestamp.desc())
        total = q.count()
        logs = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"total": total, "page": page, "page_size": page_size, "items": [log.as_dict() for log in logs]}
    finally:
        session.close()


@router.delete("/admin/ingest-log")
async def clear_ingest_log():
    session = SessionLocal()
    try:
        deleted = session.query(IngestLog).delete()
        session.commit()
        return {"deleted": deleted}
    finally:
        session.close()
