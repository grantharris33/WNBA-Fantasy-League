from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Player, RosterSlot, Team, WeeklyLineup


class LineupService:
    def __init__(self, db: Session):
        self.db = db

    def _week_bounds(self, target: date) -> tuple[datetime, datetime, int]:
        """Return UTC datetimes for Monday 00:00 - Sunday 23:59 and week-id.

        Week-id is encoded as year * 100 + iso_week so that 2025-W02 => 202502.
        This keeps it sortable and unique across seasons.
        """
        iso_year, iso_week, _ = target.isocalendar()
        week_id = iso_year * 100 + iso_week

        # Monday (weekday() == 0) at 00:00 UTC
        monday = target - timedelta(days=target.weekday())
        start = datetime.combine(monday, datetime.min.time())
        end = start + timedelta(days=7)  # exclusive upper bound (next Monday)
        return start, end, week_id

    def get_current_week_id(self) -> int:
        """Get the current week ID."""
        today = datetime.now(timezone.utc).date()
        _, _, week_id = self._week_bounds(today)
        return week_id

    def can_modify_lineup(self, team_id: int, week_id: int) -> bool:
        """Check if a lineup can be modified (not locked)."""
        current_week_id = self.get_current_week_id()

        # Can only modify current or future weeks
        if week_id < current_week_id:
            return False

        # Check if lineup is already locked
        existing_lineup = (
            self.db.query(WeeklyLineup).filter(WeeklyLineup.team_id == team_id, WeeklyLineup.week_id == week_id).first()
        )

        # If lineup exists and is locked, can't modify
        if existing_lineup:
            return False

        return True

    def lock_weekly_lineups(self, week_id: int) -> int:
        """Lock lineups for a specific week by copying current roster state.

        Returns the number of teams processed.
        """
        teams_processed = 0
        locked_at = datetime.now(timezone.utc)

        # Get all teams
        teams = self.db.query(Team).all()

        for team in teams:
            # Check if lineup is already locked for this week
            existing_lineup = (
                self.db.query(WeeklyLineup)
                .filter(WeeklyLineup.team_id == team.id, WeeklyLineup.week_id == week_id)
                .first()
            )

            if existing_lineup:
                continue  # Already locked

            # Get current roster state
            roster_slots = self.db.query(RosterSlot).filter(RosterSlot.team_id == team.id).all()

            # Create weekly lineup entries
            for slot in roster_slots:
                weekly_lineup = WeeklyLineup(
                    team_id=team.id,
                    player_id=slot.player_id,
                    week_id=week_id,
                    is_starter=slot.is_starter,
                    locked_at=locked_at,
                )
                self.db.add(weekly_lineup)

            teams_processed += 1

        self.db.commit()
        return teams_processed

    def set_weekly_starters(self, team_id: int, week_id: int, starter_ids: List[int]) -> bool:
        """Set starters for a specific week.

        Returns True if successful, False if lineup is locked.
        """
        if not self.can_modify_lineup(team_id, week_id):
            return False

        # For current week, update the roster_slot table
        current_week_id = self.get_current_week_id()
        if week_id == current_week_id:
            # Update RosterSlot table
            roster_slots = self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id).all()

            for slot in roster_slots:
                slot.is_starter = slot.player_id in starter_ids

            # Increment moves counter for the team
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if team:
                team.moves_this_week += 1

            self.db.commit()

        return True

    def get_weekly_lineup(self, team_id: int, week_id: int) -> Optional[List[dict]]:
        """Get lineup for a specific week."""
        current_week_id = self.get_current_week_id()

        # For current/future weeks, get from RosterSlot
        if week_id >= current_week_id:
            roster_slots = (
                self.db.query(RosterSlot, Player)
                .join(Player, RosterSlot.player_id == Player.id)
                .filter(RosterSlot.team_id == team_id)
                .all()
            )

            lineup = []
            for slot, player in roster_slots:
                lineup.append(
                    {
                        "player_id": player.id,
                        "player_name": player.full_name,
                        "position": player.position,
                        "team_abbr": player.team_abbr,
                        "is_starter": slot.is_starter,
                        "locked": week_id < current_week_id,
                    }
                )
            return lineup

        # For past weeks, get from WeeklyLineup
        weekly_lineups = (
            self.db.query(WeeklyLineup, Player)
            .join(Player, WeeklyLineup.player_id == Player.id)
            .filter(WeeklyLineup.team_id == team_id, WeeklyLineup.week_id == week_id)
            .all()
        )

        if not weekly_lineups:
            return None

        lineup = []
        for lineup_entry, player in weekly_lineups:
            lineup.append(
                {
                    "player_id": player.id,
                    "player_name": player.full_name,
                    "position": player.position,
                    "team_abbr": player.team_abbr,
                    "is_starter": lineup_entry.is_starter,
                    "locked": True,
                    "locked_at": lineup_entry.locked_at,
                }
            )

        return lineup

    def get_lineup_history(self, team_id: int) -> List[dict]:
        """Get all historical lineups for a team."""
        # Get all weeks with lineups
        weeks = (
            self.db.query(WeeklyLineup.week_id)
            .filter(WeeklyLineup.team_id == team_id)
            .distinct()
            .order_by(WeeklyLineup.week_id.desc())
            .all()
        )

        history = []
        current_week_id = self.get_current_week_id()

        # Add current week first if not locked
        current_lineup = self.get_weekly_lineup(team_id, current_week_id)
        if current_lineup:
            history.append({"week_id": current_week_id, "lineup": current_lineup, "is_current": True})

        # Add historical weeks
        for (week_id,) in weeks:
            if week_id == current_week_id:
                continue  # Already added above

            lineup = self.get_weekly_lineup(team_id, week_id)
            if lineup:
                history.append({"week_id": week_id, "lineup": lineup, "is_current": False})

        return history
