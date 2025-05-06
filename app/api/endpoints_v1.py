from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import League, Team, TeamScore

from .schemas import LeagueOut, Pagination, PlayerOut, ScoreOut, TeamOut

router = APIRouter(prefix="/api/v1", tags=["public"])


# ---------------------------------------------------------------------------
# Dependency: provide DB session per request
# ---------------------------------------------------------------------------


def _get_db() -> Session:  # noqa: D401
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 5-B List Leagues – GET /api/v1/leagues
# ---------------------------------------------------------------------------


@router.get("/leagues", response_model=Pagination[LeagueOut])
def list_leagues(  # noqa: D401
    *, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(_get_db)
):
    total = db.query(League).count()
    leagues = db.query(League).order_by(League.id).offset(offset).limit(limit).all()  # deterministic ordering

    items = [LeagueOut.from_orm(league) for league in leagues]
    return Pagination[LeagueOut](total=total, limit=limit, offset=offset, items=items)


# ---------------------------------------------------------------------------
# 5-C Team Detail – GET /api/v1/teams/{team_id}
# ---------------------------------------------------------------------------


@router.get("/teams/{team_id}", response_model=TeamOut)
def team_detail(*, team_id: int, db: Session = Depends(_get_db)):  # noqa: D401
    team = db.query(Team).filter_by(id=team_id).one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Roster list
    roster_players: List[PlayerOut] = [PlayerOut.from_orm(rs.player) for rs in team.roster_slots]

    # Season points = sum of all weekly scores
    season_points = sum(score.score for score in team.scores)

    return TeamOut(
        id=team.id,
        name=team.name,
        league_id=team.league_id,
        owner_id=team.owner_id,
        roster=roster_players,
        season_points=round(season_points, 2),
    )


# ---------------------------------------------------------------------------
# 5-D Current Scores – GET /api/v1/scores/current
# ---------------------------------------------------------------------------


@router.get("/scores/current", response_model=List[ScoreOut])
def current_scores(*, db: Session = Depends(_get_db)) -> List[ScoreOut]:  # noqa: D401
    # Determine latest week id (if any)
    latest_week = db.query(func.max(TeamScore.week)).scalar()

    teams = db.query(Team).all()
    result: List[ScoreOut] = []

    for team in teams:
        season_points = sum(score.score for score in team.scores)

        # Weekly delta = score of latest week if exists else 0
        latest_week_score = 0.0
        if latest_week is not None:
            for score in team.scores:
                if score.week == latest_week:
                    latest_week_score = score.score
                    break

        result.append(
            ScoreOut(
                team_id=team.id,
                team_name=team.name,
                season_points=round(season_points, 2),
                weekly_delta=round(latest_week_score, 2),
                bonuses={},  # Placeholder – future extension
            )
        )

    # Sort descending by season points
    result.sort(key=lambda s: s.season_points, reverse=True)
    return result
