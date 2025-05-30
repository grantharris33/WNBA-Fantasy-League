"""League management service."""

from __future__ import annotations

import secrets
import string
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import League, Team, User, DraftState


class LeagueService:
    """Service for managing leagues."""

    def __init__(self, db: Session):
        self.db = db

    def generate_invite_code(self) -> str:
        """Generate a unique invite code in format LEAGUE-XXXX-XXXX."""
        while True:
            # Generate 8 random alphanumeric characters
            chars = string.ascii_uppercase + string.digits
            code_part = ''.join(secrets.choice(chars) for _ in range(8))
            invite_code = f"LEAGUE-{code_part[:4]}-{code_part[4:]}"

            # Check if this code already exists
            existing = self.db.query(League).filter(League.invite_code == invite_code).first()
            if not existing:
                return invite_code

    def create_league(
        self,
        name: str,
        commissioner: User,
        max_teams: int = 12,
        draft_date: Optional[datetime] = None,
        settings: Optional[dict] = None,
    ) -> League:
        """Create a new league with the given user as commissioner."""
        # Validate max_teams
        if not 2 <= max_teams <= 12:
            raise HTTPException(status_code=400, detail="max_teams must be between 2 and 12")

        # Generate unique invite code
        invite_code = self.generate_invite_code()

        # Create league
        league = League(
            name=name,
            invite_code=invite_code,
            max_teams=max_teams,
            draft_date=draft_date,
            settings=settings or {},
            commissioner_id=commissioner.id,
            is_active=True,
        )

        self.db.add(league)
        self.db.commit()
        self.db.refresh(league)

        return league

    def update_league(
        self,
        league_id: int,
        user: User,
        name: Optional[str] = None,
        max_teams: Optional[int] = None,
        draft_date: Optional[datetime] = None,
        settings: Optional[dict] = None,
    ) -> League:
        """Update league settings. Only commissioner can update."""
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        # Check if user is commissioner
        if league.commissioner_id != user.id:
            raise HTTPException(status_code=403, detail="Only the commissioner can perform this action")

        # Check if draft has started
        draft_state = self.db.query(DraftState).filter(DraftState.league_id == league_id).first()
        if draft_state and draft_state.status in ["active", "completed"]:
            raise HTTPException(status_code=400, detail="Cannot modify league after draft starts")

        # Validate max_teams if provided
        if max_teams is not None:
            if not 2 <= max_teams <= 12:
                raise HTTPException(status_code=400, detail="max_teams must be between 2 and 12")

            # Cannot reduce below current team count
            current_team_count = self.db.query(Team).filter(Team.league_id == league_id).count()
            if max_teams < current_team_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reduce max_teams below current team count ({current_team_count})"
                )

        # Update fields
        if name is not None:
            league.name = name
        if max_teams is not None:
            league.max_teams = max_teams
        if draft_date is not None:
            league.draft_date = draft_date
        if settings is not None:
            league.settings = settings

        self.db.commit()
        self.db.refresh(league)

        return league

    def delete_league(self, league_id: int, user: User) -> None:
        """Delete a league. Only commissioner can delete and only if draft hasn't started."""
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        # Check if user is commissioner
        if league.commissioner_id != user.id:
            raise HTTPException(status_code=403, detail="Only the commissioner can perform this action")

        # Check if draft has started
        draft_state = self.db.query(DraftState).filter(DraftState.league_id == league_id).first()
        if draft_state and draft_state.status in ["active", "completed"]:
            raise HTTPException(status_code=400, detail="Cannot delete league after draft starts")

        # Delete league (cascades to teams)
        self.db.delete(league)
        self.db.commit()

    def join_league(self, invite_code: str, team_name: str, user: User) -> Team:
        """Join a league using invite code and create a team."""
        # Find league by invite code
        league = self.db.query(League).filter(League.invite_code == invite_code).first()
        if not league:
            raise HTTPException(status_code=404, detail="Invalid or expired invite code")

        if not league.is_active:
            raise HTTPException(status_code=400, detail="League is not active")

        # Check if league is full
        current_team_count = self.db.query(Team).filter(Team.league_id == league.id).count()
        if current_team_count >= league.max_teams:
            raise HTTPException(status_code=409, detail="League has reached maximum capacity")

        # Check if user already has a team in this league
        existing_team = (
            self.db.query(Team)
            .filter(Team.league_id == league.id, Team.owner_id == user.id)
            .first()
        )
        if existing_team:
            raise HTTPException(status_code=409, detail="You already have a team in this league")

        # Check if team name is already taken in this league
        existing_name = (
            self.db.query(Team)
            .filter(Team.league_id == league.id, Team.name == team_name)
            .first()
        )
        if existing_name:
            raise HTTPException(status_code=409, detail="Team name already taken in this league")

        # Create team
        team = Team(
            name=team_name,
            owner_id=user.id,
            league_id=league.id,
            moves_this_week=0,
        )

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        return team

    def leave_league(self, league_id: int, team_id: int, user: User) -> None:
        """Remove a team from a league."""
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        team = self.db.query(Team).filter(Team.id == team_id, Team.league_id == league_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Check permissions: user can remove their own team, commissioner can remove any team
        if team.owner_id != user.id and league.commissioner_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Check if draft has started
        draft_state = self.db.query(DraftState).filter(DraftState.league_id == league_id).first()
        if draft_state and draft_state.status in ["active", "completed"]:
            raise HTTPException(status_code=400, detail="Cannot leave league after draft starts")

        # Delete team
        self.db.delete(team)
        self.db.commit()

    def generate_new_invite_code(self, league_id: int, user: User) -> str:
        """Generate a new invite code for the league. Commissioner only."""
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        # Check if user is commissioner
        if league.commissioner_id != user.id:
            raise HTTPException(status_code=403, detail="Only the commissioner can perform this action")

        # Generate new invite code
        new_invite_code = self.generate_invite_code()
        league.invite_code = new_invite_code

        self.db.commit()
        self.db.refresh(league)

        return new_invite_code

    def get_league_details(self, league_id: int, user: User) -> League:
        """Get league details. Include invite_code only if user is commissioner."""
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        return league

    def get_user_leagues(self, user: User) -> List[dict]:
        """Get all leagues where user has a team or is commissioner."""
        # Get leagues where user is commissioner
        owned_leagues = (
            self.db.query(League)
            .filter(League.commissioner_id == user.id)
            .all()
        )

        # Get leagues where user has a team
        team_leagues = (
            self.db.query(League)
            .join(Team, Team.league_id == League.id)
            .filter(Team.owner_id == user.id)
            .all()
        )

        # Combine and deduplicate
        all_leagues = {league.id: league for league in owned_leagues + team_leagues}

        # Build response with role information
        result = []
        for league in all_leagues.values():
            role = "commissioner" if league.commissioner_id == user.id else "member"
            result.append({
                "league": league,
                "role": role,
            })

        return result