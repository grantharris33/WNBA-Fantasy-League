from __future__ import annotations

from datetime import datetime as _dt
from typing import Optional as _Optional

import anyio  # lightweight concurrency helper
from fastapi import APIRouter, HTTPException

from app.core.database import SessionLocal
from app.jobs.ingest import ingest_stat_lines as _ingest_stat_lines
from app.models import IngestionQueue, IngestionRun, IngestLog
from app.services.backfill import BackfillService
from app.services.scoring import update_weekly_team_scores as _update_weekly_team_scores

from .admin import router as admin_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .draft import router as draft_router
from .endpoints_v1 import router as v1_router
from .game_router import router as game_router
from .league_management import router as league_management_router
from .league_router import router as league_router
from .logs import router as logs_router
from .lookup import router as lookup_router
from .scores import router as scores_router
from .users import router as users_router
from .wnba import router as wnba_router

router = APIRouter()

# Auth endpoints
router.include_router(auth_router, prefix="/api/v1")

# Users endpoints
router.include_router(users_router, prefix="/api/v1")

# Scores endpoints
router.include_router(scores_router, prefix="/api/v1")

# Draft endpoints
router.include_router(draft_router, prefix="/api/v1")

# League management endpoints
router.include_router(league_management_router)

# Logs endpoints
router.include_router(logs_router)

# Analytics endpoints
router.include_router(analytics_router)

# Admin endpoints
router.include_router(admin_router)

# V1 public endpoints
router.include_router(v1_router)
router.include_router(game_router, prefix="/api/v1")
router.include_router(league_router, prefix="/api/v1")

# WNBA data endpoints
router.include_router(wnba_router)

# Lookup endpoints
router.include_router(lookup_router)


@router.get("/health")
async def health():
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with database and external service verification."""
    from sqlalchemy import text
    from app.external_apis.rapidapi_client import wnba_client
    import os
    
    health_status = {
        "status": "ok",
        "timestamp": _dt.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "database": {"status": "unknown", "message": ""},
            "rapidapi": {"status": "unknown", "message": ""},
            "scheduler": {"status": "unknown", "message": ""},
            "disk_space": {"status": "unknown", "message": ""}
        }
    }
    
    # Check database
    session = SessionLocal()
    try:
        result = session.execute(text("SELECT 1"))
        result.scalar()
        session.execute(text("SELECT COUNT(*) FROM user"))
        health_status["checks"]["database"] = {"status": "healthy", "message": "Connected and operational"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
    finally:
        session.close()
    
    # Check RapidAPI connectivity (if key is configured)
    if os.getenv("RAPIDAPI_KEY"):
        try:
            # Just check if we can reach the API
            test_date = _dt.now()
            await wnba_client.fetch_schedule(
                test_date.strftime("%Y"),
                test_date.strftime("%m"), 
                test_date.strftime("%d")
            )
            health_status["checks"]["rapidapi"] = {"status": "healthy", "message": "API accessible"}
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["checks"]["rapidapi"] = {"status": "unhealthy", "message": str(e)}
        finally:
            await wnba_client.close()
    else:
        health_status["checks"]["rapidapi"] = {"status": "unconfigured", "message": "No API key"}
    
    # Check scheduler
    from app.core.scheduler import scheduler
    if scheduler and scheduler.running:
        job_count = len(scheduler.get_jobs())
        health_status["checks"]["scheduler"] = {
            "status": "healthy", 
            "message": f"Running with {job_count} jobs"
        }
    else:
        health_status["status"] = "degraded"
        health_status["checks"]["scheduler"] = {"status": "unhealthy", "message": "Not running"}
    
    # Check disk space
    try:
        import shutil
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024 ** 3)
        percent_used = (usage.used / usage.total) * 100
        
        if free_gb < 1:  # Less than 1GB free
            health_status["status"] = "degraded"
            health_status["checks"]["disk_space"] = {
                "status": "critical",
                "message": f"Only {free_gb:.2f}GB free ({percent_used:.1f}% used)"
            }
        elif free_gb < 5:  # Less than 5GB free
            health_status["checks"]["disk_space"] = {
                "status": "warning",
                "message": f"{free_gb:.2f}GB free ({percent_used:.1f}% used)"
            }
        else:
            health_status["checks"]["disk_space"] = {
                "status": "healthy",
                "message": f"{free_gb:.2f}GB free ({percent_used:.1f}% used)"
            }
    except Exception as e:
        health_status["checks"]["disk_space"] = {"status": "unknown", "message": str(e)}
    
    return health_status


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

    try:
        await _ingest_stat_lines(target_date)
        return {"status": "ingest_completed", "date": (target_date or "auto")}  # type: ignore[arg-type]
    except Exception as e:
        # Log the error
        session = SessionLocal()
        try:
            ingest_log = IngestLog(provider="admin_api", message=f"ERROR: Manual ingest failed: {str(e)}")
            session.add(ingest_log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@router.get("/admin/ingest/test")
async def test_ingest_connectivity():
    """Test ingest system connectivity and configuration."""
    import os

    from app.external_apis.rapidapi_client import wnba_client

    diagnostics = {
        "api_key_configured": bool(os.getenv("WNBA_API_KEY") or os.getenv("RAPIDAPI_KEY")),
        "api_key_partial": None,
        "connectivity_test": None,
        "sample_date_test": None,
    }

    # Show partial API key for verification
    api_key = os.getenv("WNBA_API_KEY") or os.getenv("RAPIDAPI_KEY")
    if api_key:
        diagnostics["api_key_partial"] = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"

    try:
        # Test basic connectivity with a recent date that should have games
        test_games = await wnba_client.fetch_schedule("2024", "05", "15")
        diagnostics["connectivity_test"] = "SUCCESS"
        diagnostics["sample_games_found"] = len(test_games) if test_games else 0
    except Exception as e:
        diagnostics["connectivity_test"] = f"FAILED: {str(e)}"

    try:
        # Test today's date (might have no games, but should not error)
        from datetime import datetime

        today = datetime.now()
        today_games = await wnba_client.fetch_schedule(today.strftime("%Y"), today.strftime("%m"), today.strftime("%d"))
        diagnostics["sample_date_test"] = "SUCCESS"
        diagnostics["today_games_found"] = len(today_games) if today_games else 0
    except Exception as e:
        diagnostics["sample_date_test"] = f"FAILED: {str(e)}"

    await wnba_client.close()
    return diagnostics


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


# ---------------------------------------------------------------------------
# Backfill & Recovery Admin Endpoints
# ---------------------------------------------------------------------------


@router.post("/admin/backfill/season/{year}")
async def backfill_season(
    year: int, start_date: _Optional[str] = None, end_date: _Optional[str] = None, dry_run: bool = False
):
    """Trigger season backfill via API."""
    start_date_obj = None
    end_date_obj = None

    if start_date:
        try:
            start_date_obj = _dt.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format – use YYYY-MM-DD")

    if end_date:
        try:
            end_date_obj = _dt.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format – use YYYY-MM-DD")

    async with BackfillService() as service:
        run_dict = await service.backfill_season(
            year=year, start_date=start_date_obj, end_date=end_date_obj, dry_run=dry_run
        )
        return run_dict


@router.get("/admin/ingestion/health")
async def ingestion_health(days_back: int = 7):
    """Get ingestion system health metrics."""
    async with BackfillService() as service:
        health_data = service.get_ingestion_health(days_back)
        return health_data


@router.post("/admin/ingestion/reprocess/{game_id}")
async def reprocess_game(game_id: str, force: bool = False):
    """Reprocess a specific game."""
    async with BackfillService() as service:
        result = await service.reprocess_game(game_id, force)
        return result


@router.get("/admin/ingestion/runs")
async def get_ingestion_runs(limit: int = 50):
    """Get recent ingestion runs."""
    session = SessionLocal()
    try:
        runs = session.query(IngestionRun).order_by(IngestionRun.start_time.desc()).limit(limit).all()
        return [run.as_dict() for run in runs]
    finally:
        session.close()


@router.get("/admin/ingestion/queue")
async def get_ingestion_queue(status: _Optional[str] = None, limit: int = 100):
    """Get ingestion queue items."""
    session = SessionLocal()
    try:
        query = session.query(IngestionQueue)
        if status:
            query = query.filter(IngestionQueue.status == status)

        queue_items = query.order_by(IngestionQueue.priority.desc(), IngestionQueue.id).limit(limit).all()
        return [item.as_dict() for item in queue_items]
    finally:
        session.close()


@router.delete("/admin/ingestion/queue/{queue_id}")
async def delete_queue_item(queue_id: int):
    """Delete a specific queue item."""
    session = SessionLocal()
    try:
        item = session.query(IngestionQueue).filter(IngestionQueue.id == queue_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Queue item not found")

        session.delete(item)
        session.commit()
        return {"status": "deleted", "queue_id": queue_id}
    finally:
        session.close()


@router.post("/admin/ingestion/find-missing")
async def find_missing_games(start_date: str, end_date: str):
    """Find missing games in a date range."""
    try:
        start_date_obj = _dt.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = _dt.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format – use YYYY-MM-DD")

    async with BackfillService() as service:
        missing_games = await service.find_missing_games(start_date_obj, end_date_obj)
        result = {
            "start_date": start_date,
            "end_date": end_date,
            "missing_games": missing_games,
            "count": len(missing_games),
        }
        return result
