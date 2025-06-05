from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import ScoreUpdateResponse, UserOut
from app.core.database import get_db
from app.models import Team, User
from app.services.scoring import update_weekly_team_scores

router = APIRouter(prefix="/scores", tags=["scores"])


@router.post("/update", response_model=ScoreUpdateResponse)
async def update_scores_manual(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    target_date: date | None = None,
):
    """
    Manually trigger score update for the current week.

    Any authenticated user can trigger a score update for their teams.
    Admins can update all teams.
    """
    # Use current date if not specified
    if target_date is None:
        target_date = datetime.utcnow().date()

    try:
        # Run the scoring update
        update_weekly_team_scores(target_date, session=db)

        # Get affected teams count
        if current_user.is_admin:
            team_count = db.query(Team).count()
            message = f"Successfully updated scores for all {team_count} teams"
        else:
            # For regular users, show their team count
            team_count = db.query(Team).filter(Team.owner_id == current_user.id).count()
            message = f"Successfully updated scores for your {team_count} team(s)"

        return ScoreUpdateResponse(
            success=True, message=message, updated_at=datetime.utcnow(), week_updated=target_date.isocalendar()[1]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update scores: {str(e)}"
        )
