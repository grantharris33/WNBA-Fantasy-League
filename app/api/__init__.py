from __future__ import annotations

from datetime import datetime as _dt
from typing import Optional as _Optional

import anyio  # lightweight concurrency helper
from fastapi import APIRouter, HTTPException

from app.core.database import SessionLocal
from app.jobs.ingest import ingest_stat_lines as _ingest_stat_lines
from app.models import IngestLog
from app.services.scoring import update_weekly_team_scores as _update_weekly_team_scores

from .endpoints_v1 import router as v1_router

router = APIRouter()

# V1 public endpoints
router.include_router(v1_router)


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


# ---------------------------------------------------------------------------
# Admin triggers – manual ingest & scoring
# ---------------------------------------------------------------------------


@router.post("/admin/ingest/run")
async def run_ingest(date: _Optional[str] = None):  # noqa: D401
    """Manually trigger stats ingest for a given ISO date (default=UTC-yesterday)."""

    target_date = None
    if date:
        try:
            target_date = _dt.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format – use YYYY-MM-DD")

    await _ingest_stat_lines(target_date)
    return {"status": "ingest_completed", "date": (target_date or "auto")}  # type: ignore[arg-type]


@router.post("/admin/scores/recompute")
async def recompute_scores(date: _Optional[str] = None):  # noqa: D401
    """Recalculate weekly team scores for ISO week containing *date* (default=UTC-yesterday)."""

    target_date = None
    if date:
        try:
            target_date = _dt.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format – use YYYY-MM-DD")

    # Run sync function in a thread so we don't block event loop
    await anyio.to_thread.run_sync(_update_weekly_team_scores, target_date)

    return {"status": "scores_recomputed", "date": (target_date or "auto")}
