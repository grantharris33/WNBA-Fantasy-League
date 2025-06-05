from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models import TransactionLog, IngestLog, User

router = APIRouter(prefix="/api/v1", tags=["logs"])


@router.get("/logs", response_model=List[dict])
async def get_logs(
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[dict]:
    """
    Get paginated transaction logs.
    Requires admin privileges.
    """
    logs = db.query(TransactionLog).order_by(desc(TransactionLog.timestamp)).offset(offset).limit(limit).all()

    result = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "method": log.method,
            "path": log.path,
        }

        # Only include patch if it exists
        if log.patch:
            log_dict["patch"] = log.patch

        # Include user email if available
        if log.user:
            log_dict["user_email"] = log.user.email

        result.append(log_dict)

    return result


@router.get("/logs/ingest", response_model=List[dict])
async def get_ingest_logs(
    current_user: Annotated[User, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    provider: Optional[str] = Query(None, description="Filter by provider (rapidapi, data_quality, etc.)"),
) -> List[dict]:
    """
    Get paginated ingest logs.
    Requires admin privileges.
    """
    query = db.query(IngestLog).order_by(desc(IngestLog.timestamp))
    
    if provider:
        query = query.filter(IngestLog.provider == provider)
    
    logs = query.offset(offset).limit(limit).all()

    return [log.as_dict() for log in logs]
