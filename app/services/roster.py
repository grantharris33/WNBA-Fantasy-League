from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models import League, Player, RosterSlot, Team, TransactionLog, User


class RosterService:
    def __init__(self, db: Session):
        self.db = db

    def get_free_agents(self, league_id: int, page: int = 1, limit: int = 100) -> List[Player]:
        """Get players not currently on any team in the league."""
        # Find all player_ids that are in a roster_slot for the given league
        roster_subquery = (
            select(RosterSlot.player_id)
            .join(Team, RosterSlot.team_id == Team.id)
            .where(Team.league_id == league_id)
            .subquery()
        )

        # Find players that are not in the roster_subquery
        query = (
            select(Player)
            .where(not_(Player.id.in_(select(roster_subquery))))
            .order_by(Player.full_name)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        return list(self.db.execute(query).scalars().all())

    def add_player_to_team(
        self, team_id: int, player_id: int, set_as_starter: bool = False, user_id: Optional[int] = None
    ) -> RosterSlot:
        """Add a free agent to a team's roster."""
        # Get the team and verify it exists
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Verify that we haven't reached the weekly move cap
        if team.moves_this_week >= 3:
            raise ValueError("Weekly move limit reached (3 moves per week)")

        # Verify player exists
        player = self.db.get(Player, player_id)
        if not player:
            raise ValueError(f"Player with ID {player_id} not found")

        # Verify player is a free agent in this league
        is_on_roster = self.db.query(
            exists().where(
                and_(RosterSlot.player_id == player_id, RosterSlot.team_id == Team.id, Team.league_id == team.league_id)
            )
        ).scalar()
        if is_on_roster:
            raise ValueError(f"Player {player.full_name} is already on a roster in this league")

        # Verify team roster size is not exceeded (max 10 players per team)
        roster_count = self.db.query(func.count(RosterSlot.id)).filter(RosterSlot.team_id == team_id).scalar()
        if roster_count >= 10:
            raise ValueError("Team roster is full (10 players maximum)")

        # Create the roster slot
        roster_slot = RosterSlot(
            team_id=team_id, player_id=player_id, position=player.position, is_starter=set_as_starter
        )

        # If player is set as starter, increment the moves_this_week counter
        if set_as_starter:
            team.moves_this_week += 1

        self.db.add(roster_slot)

        # Create transaction log
        action = f"ADD {player.full_name} to {team.name}"
        if set_as_starter:
            action += " (set as starter)"

        self.db.add(TransactionLog(user_id=user_id, action=action, timestamp=datetime.utcnow()))

        self.db.commit()
        return roster_slot

    def drop_player_from_team(self, team_id: int, player_id: int, user_id: Optional[int] = None) -> None:
        """Remove a player from a team's roster."""
        # Get the team and verify it exists
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Verify the player is on the team
        roster_slot = (
            self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.player_id == player_id).first()
        )

        if not roster_slot:
            raise ValueError(f"Player with ID {player_id} is not on team with ID {team_id}")

        # Get player name for the log
        player = self.db.get(Player, player_id)

        # Delete the roster slot
        self.db.delete(roster_slot)

        # Create transaction log
        self.db.add(
            TransactionLog(
                user_id=user_id, action=f"DROP {player.full_name} from {team.name}", timestamp=datetime.utcnow()
            )
        )

        self.db.commit()

    def set_starters(
        self, team_id: int, starter_player_ids: List[int], user_id: Optional[int] = None
    ) -> List[RosterSlot]:  # noqa: C901
        """Set the starting lineup for a team."""
        # Get the team and verify it exists
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Verify that all players are on the team
        team_roster_query = self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id).all()
        team_player_ids = [rs.player_id for rs in team_roster_query]

        for player_id in starter_player_ids:
            if player_id not in team_player_ids:
                raise ValueError(f"Player with ID {player_id} is not on team with ID {team_id}")

        # Verify that the correct number of starters is provided (5)
        if len(starter_player_ids) != 5:
            raise ValueError("A valid starting lineup must have exactly 5 players")

        # Get the player positions to verify positional legality
        players = self.db.query(Player).filter(Player.id.in_(starter_player_ids)).all()
        player_positions = [p.position for p in players if p.position]

        # Check positional requirements: ≥2 Guards (G) AND ≥1 Forward (F) or Forward/Center (F-C)
        guard_count = sum(1 for pos in player_positions if pos and 'G' in pos)
        forward_count = sum(1 for pos in player_positions if pos and ('F' in pos or 'C' in pos))

        if guard_count < 2:
            raise ValueError("Starting lineup must include at least 2 players with Guard (G) position")

        if forward_count < 1:
            raise ValueError(
                "Starting lineup must include at least 1 player with Forward (F) or Forward/Center (F-C) position"
            )

        # Get current starters
        current_starters = (
            self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.is_starter == 1).all()
        )
        current_starter_ids = [rs.player_id for rs in current_starters]

        # Count how many new players are being promoted to starter
        new_starter_count = sum(1 for pid in starter_player_ids if pid not in current_starter_ids)

        # Check if we have enough moves left for the week
        if new_starter_count > (3 - team.moves_this_week):
            raise ValueError(
                f"Not enough moves left for the week. You're trying to add {new_starter_count} new starters but only have {3 - team.moves_this_week} moves left."
            )

        # Update is_starter for all roster slots
        for rs in team_roster_query:
            old_status = rs.is_starter
            new_status = rs.player_id in starter_player_ids

            # Update only if there's a change
            if old_status != new_status:
                rs.is_starter = new_status

                # Only increment moves_this_week when setting a player TO starter
                if new_status:
                    team.moves_this_week += 1
                    # Log the transaction
                    player = self.db.get(Player, rs.player_id)
                    self.db.add(
                        TransactionLog(
                            user_id=user_id,
                            action=f"START {player.full_name} on {team.name}",
                            timestamp=datetime.utcnow(),
                        )
                    )
                else:
                    # Log bench transaction but don't count it as a move
                    player = self.db.get(Player, rs.player_id)
                    self.db.add(
                        TransactionLog(
                            user_id=user_id,
                            action=f"BENCH {player.full_name} on {team.name}",
                            timestamp=datetime.utcnow(),
                        )
                    )

        self.db.commit()

        # Return updated roster slots that are starters
        return self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.is_starter == 1).all()

    def reset_weekly_moves(self) -> None:
        """Reset the moves_this_week counter for all teams."""
        self.db.query(Team).update({Team.moves_this_week: 0})
        self.db.commit()

    def get_roster(self, team_id: int, include_player_details: bool = False) -> List[dict]:
        """
        Get the roster for a team, optionally including player details
        """
        # Get all the roster slots for a team
        roster_slots = self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id).all()

        # Format the output
        roster = []
        for slot in roster_slots:
            slot_data = {
                "id": slot.id,
                "player_id": slot.player_id,
                "position": slot.position,
                "is_starter": slot.is_starter == 1,
            }

            if include_player_details:
                player = self.db.query(Player).filter(Player.id == slot.player_id).first()
                if player:
                    slot_data["player"] = {
                        "id": player.id,
                        "full_name": player.full_name,
                        "position": player.position,
                        "team_abbr": player.team_abbr,
                    }

            roster.append(slot_data)

        # Sort by is_starter descending, then id
        roster.sort(key=lambda x: (not x["is_starter"], x["id"]))
        return roster
