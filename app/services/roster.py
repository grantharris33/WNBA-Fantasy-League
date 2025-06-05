from datetime import datetime, timezone, timedelta, date
from typing import List, Optional

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models import League, Player, RosterSlot, Team, TransactionLog, User, AdminMoveGrant, WeeklyLineup


class RosterService:
    def __init__(self, db: Session):
        self.db = db

    def _get_current_week_id(self) -> int:
        """Get the current week ID based on ISO calendar."""
        today = datetime.now(timezone.utc).date()
        iso_year, iso_week, _ = today.isocalendar()
        return iso_year * 100 + iso_week

    def get_free_agents(self, league_id: int) -> List[Player]:
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
        )

        return list(self.db.execute(query).scalars().all())

    def _should_auto_set_as_starter(self, team_id: int, new_player: Player) -> bool:
        """
        Determine if a new player should be automatically set as a starter.

        Rules:
        1. Must have fewer than 5 current starters
        2. Adding this player must not violate position requirements
        3. If we have <5 starters total, auto-add if it helps meet requirements
        """
        # Get current starters
        current_starters = (
            self.db.query(RosterSlot)
            .join(Player, RosterSlot.player_id == Player.id)
            .filter(RosterSlot.team_id == team_id, RosterSlot.is_starter == True)
            .all()
        )

        # If we already have 5 starters, don't auto-add
        if len(current_starters) >= 5:
            return False

        # Get current starter positions
        current_positions = [rs.player.position for rs in current_starters if rs.player.position]

        # Count current position requirements
        current_guards = sum(1 for pos in current_positions if pos and 'G' in pos)
        current_forwards_centers = sum(1 for pos in current_positions if pos and ('F' in pos or 'C' in pos))

        # If adding this player, what would the counts be?
        new_position = new_player.position
        current_guards + (1 if new_position and 'G' in new_position else 0)
        current_forwards_centers + (1 if new_position and ('F' in new_position or 'C' in new_position) else 0)

        # Auto-add if:
        # 1. We have fewer than 5 starters AND
        # 2. Either we need more guards and this is a guard, OR we need more F/C and this is F/C, OR
        # 3. We already meet requirements but still need to fill roster spots

        starters_count = len(current_starters)

        # If we have 0-1 starters, definitely add
        if starters_count <= 1:
            return True

        # If we don't have enough guards yet and this is a guard
        if current_guards < 2 and new_position and 'G' in new_position:
            return True

        # If we don't have any forwards/centers yet and this is one
        if current_forwards_centers < 1 and new_position and ('F' in new_position or 'C' in new_position):
            return True

        # If we meet position requirements but still need more starters (up to 5)
        if current_guards >= 2 and current_forwards_centers >= 1 and starters_count < 5:
            return True

        return False

    def add_player_to_team(
        self, team_id: int, player_id: int, set_as_starter: bool = False, user_id: Optional[int] = None
    ) -> RosterSlot:
        """Add a free agent to a team's roster."""
        # Get the team and verify it exists
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Check move limits only if setting as starter
        if set_as_starter:
            current_week = self._get_current_week_id()
            total_available_moves = self._get_total_available_moves(team_id, current_week)

            # Verify that we haven't reached the weekly move cap
            if team.moves_this_week >= total_available_moves:
                raise ValueError(f"Weekly move limit reached ({team.moves_this_week}/{total_available_moves} moves used)")

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

        # Determine if player should be auto-set as starter (if not explicitly requested)
        auto_starter = False
        if not set_as_starter:
            auto_starter = self._should_auto_set_as_starter(team_id, player)
            if auto_starter:
                # Check move limits for auto-starter
                current_week = self._get_current_week_id()
                total_available_moves = self._get_total_available_moves(team_id, current_week)
                if team.moves_this_week >= total_available_moves:
                    # Don't auto-set as starter if no moves left
                    auto_starter = False
                else:
                    set_as_starter = True

        # Create the roster slot
        roster_slot = RosterSlot(
            team_id=team_id, player_id=player_id, position=player.position, is_starter=set_as_starter
        )

        # Increment the moves counter only if player is set as starter
        if set_as_starter:
            team.moves_this_week += 1

        self.db.add(roster_slot)

        # Create transaction log
        action = f"ADD {player.full_name} to {team.name}"
        if set_as_starter:
            action += " (auto-set as starter)" if auto_starter else " (set as starter)"

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

        # Delete the roster slot (dropping players no longer counts as a move)
        self.db.delete(roster_slot)

        # Create transaction log
        self.db.add(
            TransactionLog(
                user_id=user_id, action=f"DROP {player.full_name} from {team.name}", timestamp=datetime.utcnow()
            )
        )

        self.db.commit()

    def _get_total_available_moves(self, team_id: int, week_id: int) -> int:
        """Calculate total available moves including admin grants for a specific week."""
        team = self.db.get(Team, team_id)
        if not team:
            return 0

        # Base weekly moves allowance
        base_moves = 3

        # Get admin-granted moves for this week
        admin_grants = (
            self.db.query(func.sum(AdminMoveGrant.moves_granted))
            .filter(AdminMoveGrant.team_id == team_id, AdminMoveGrant.week_id == week_id)
            .scalar() or 0
        )

        return base_moves + admin_grants

    def get_team_move_summary(self, team_id: int, week_id: int) -> dict:
        """Get detailed move summary for a team including admin grants."""
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        base_moves = 3
        admin_grants = (
            self.db.query(func.sum(AdminMoveGrant.moves_granted))
            .filter(AdminMoveGrant.team_id == team_id, AdminMoveGrant.week_id == week_id)
            .scalar() or 0
        )
        total_available = base_moves + admin_grants
        moves_used = team.moves_this_week
        moves_remaining = total_available - moves_used

        # Get admin grant details
        admin_grant_records = (
            self.db.query(AdminMoveGrant)
            .filter(AdminMoveGrant.team_id == team_id, AdminMoveGrant.week_id == week_id)
            .all()
        )

        return {
            "team_id": team_id,
            "week_id": week_id,
            "base_moves": base_moves,
            "admin_granted_moves": admin_grants,
            "total_available_moves": total_available,
            "moves_used": moves_used,
            "moves_remaining": moves_remaining,
            "admin_grants": [
                {
                    "id": grant.id,
                    "moves_granted": grant.moves_granted,
                    "reason": grant.reason,
                    "granted_at": grant.granted_at,
                    "admin_user_id": grant.admin_user_id,
                }
                for grant in admin_grant_records
            ]
        }

    def grant_admin_moves(
        self,
        team_id: int,
        week_id: int,
        moves_to_grant: int,
        reason: str,
        admin_user_id: int
    ) -> AdminMoveGrant:
        """Grant additional moves to a team for a specific week."""
        # Verify admin user exists and is admin
        admin_user = self.db.get(User, admin_user_id)
        if not admin_user:
            raise ValueError(f"Admin user with ID {admin_user_id} not found")
        if not admin_user.is_admin:
            raise ValueError(f"User with ID {admin_user_id} is not an admin")

        # Verify team exists
        team = self.db.get(Team, team_id)
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Validate inputs
        if moves_to_grant <= 0:
            raise ValueError("Must grant at least 1 move")
        if not reason.strip():
            raise ValueError("Reason is required")

        # Create the grant record
        grant = AdminMoveGrant(
            team_id=team_id,
            admin_user_id=admin_user_id,
            moves_granted=moves_to_grant,
            reason=reason.strip(),
            week_id=week_id
        )

        self.db.add(grant)

        # Create transaction log
        self.db.add(TransactionLog(
            user_id=admin_user_id,
            action=f"ADMIN GRANT {moves_to_grant} moves to {team.name} for week {week_id}: {reason}",
            timestamp=datetime.utcnow()
        ))

        self.db.commit()
        return grant

    def set_starters_admin_override(
        self,
        team_id: int,
        starter_player_ids: List[int],
        admin_user_id: int,
        week_id: int,
        bypass_move_limit: bool = True
    ) -> List[RosterSlot]:
        """Set starters with admin override capability."""
        # Verify admin user exists and is admin
        admin_user = self.db.get(User, admin_user_id)
        if not admin_user:
            raise ValueError(f"Admin user with ID {admin_user_id} not found")
        if not admin_user.is_admin:
            raise ValueError(f"User with ID {admin_user_id} is not an admin")

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

        # Check move limits unless bypassing
        if not bypass_move_limit:
            total_available_moves = self._get_total_available_moves(team_id, week_id)
            if new_starter_count > (total_available_moves - team.moves_this_week):
                raise ValueError(
                    f"Not enough moves left for the week. You're trying to add {new_starter_count} new starters but only have {total_available_moves - team.moves_this_week} moves left."
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
                    if not bypass_move_limit:
                        team.moves_this_week += 1

                    # Log the transaction with admin override indication
                    player = self.db.get(Player, rs.player_id)
                    action = f"START {player.full_name} on {team.name}"
                    if bypass_move_limit:
                        action += " (ADMIN OVERRIDE)"

                    self.db.add(
                        TransactionLog(
                            user_id=admin_user_id,
                            action=action,
                            timestamp=datetime.utcnow(),
                        )
                    )
                else:
                    # Log bench transaction but don't count it as a move
                    player = self.db.get(Player, rs.player_id)
                    action = f"BENCH {player.full_name} on {team.name}"
                    if bypass_move_limit:
                        action += " (ADMIN OVERRIDE)"

                    self.db.add(
                        TransactionLog(
                            user_id=admin_user_id,
                            action=action,
                            timestamp=datetime.utcnow(),
                        )
                    )

        self.db.commit()

        # Return updated roster slots that are starters
        return self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id, RosterSlot.is_starter == 1).all()

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

        # Check if we have enough moves left for the week (including admin grants)
        current_week = self._get_current_week_id()
        total_available_moves = self._get_total_available_moves(team_id, current_week)

        if new_starter_count > (total_available_moves - team.moves_this_week):
            raise ValueError(
                f"Not enough moves left for the week. You're trying to add {new_starter_count} new starters but only have {total_available_moves - team.moves_this_week} moves left."
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

    def save_current_starters_to_history(self, week_id: int) -> int:
        """
        Save current starter status for all teams to WeeklyLineup for the given week.
        Returns the number of teams processed.
        """
        teams_processed = 0
        locked_at = datetime.now(timezone.utc)

        # Get all teams
        teams = self.db.query(Team).all()

        for team in teams:
            # Check if lineup is already saved for this week
            existing_lineup = (
                self.db.query(WeeklyLineup)
                .filter(WeeklyLineup.team_id == team.id, WeeklyLineup.week_id == week_id)
                .first()
            )

            if existing_lineup:
                continue  # Already saved

            # Get current roster state
            roster_slots = (
                self.db.query(RosterSlot)
                .filter(RosterSlot.team_id == team.id)
                .all()
            )

            # Save weekly lineup entries
            for slot in roster_slots:
                weekly_lineup = WeeklyLineup(
                    team_id=team.id,
                    player_id=slot.player_id,
                    week_id=week_id,
                    is_starter=slot.is_starter,
                    locked_at=locked_at
                )
                self.db.add(weekly_lineup)

            teams_processed += 1

        self.db.commit()
        return teams_processed

    def carry_over_starters_from_previous_week(self, current_week_id: int) -> int:
        """
        Carry over starters from the previous week for teams that don't have any starters set.
        Returns the number of teams processed.
        """
        teams_processed = 0
        previous_week_id = current_week_id - 1

        # Get all teams
        teams = self.db.query(Team).all()

        for team in teams:
            # Check if team has any current starters
            current_starters = (
                self.db.query(RosterSlot)
                .filter(RosterSlot.team_id == team.id, RosterSlot.is_starter == True)
                .count()
            )

            if current_starters > 0:
                continue  # Team already has starters set for this week

            # Get starters from previous week
            previous_starters = (
                self.db.query(WeeklyLineup)
                .filter(
                    WeeklyLineup.team_id == team.id,
                    WeeklyLineup.week_id == previous_week_id,
                    WeeklyLineup.is_starter == True
                )
                .all()
            )

            if not previous_starters:
                continue  # No previous week starters to carry over

            # Carry over starters if the players are still on the roster
            for prev_starter in previous_starters:
                roster_slot = (
                    self.db.query(RosterSlot)
                    .filter(
                        RosterSlot.team_id == team.id,
                        RosterSlot.player_id == prev_starter.player_id
                    )
                    .first()
                )

                if roster_slot:
                    roster_slot.is_starter = True

            teams_processed += 1

        self.db.commit()
        return teams_processed

    def ensure_starters_carried_over(self, team_id: int) -> bool:
        """
        Ensure that a team has starters carried over from the previous week if they don't have any current starters.
        This can be called manually to fix teams that might not have had starters during the weekly reset.
        Returns True if starters were carried over, False otherwise.
        """
        # Check if team has any current starters
        current_starters = (
            self.db.query(RosterSlot)
            .filter(RosterSlot.team_id == team_id, RosterSlot.is_starter == True)
            .count()
        )

        if current_starters > 0:
            return False  # Team already has starters set

        # Get current and previous week IDs
        current_week_id = self._get_current_week_id()
        previous_week_id = current_week_id - 1

        # Get starters from previous week
        previous_starters = (
            self.db.query(WeeklyLineup)
            .filter(
                WeeklyLineup.team_id == team_id,
                WeeklyLineup.week_id == previous_week_id,
                WeeklyLineup.is_starter == True
            )
            .all()
        )

        if not previous_starters:
            return False  # No previous week starters to carry over

        # Carry over starters if the players are still on the roster
        carried_over = False
        for prev_starter in previous_starters:
            roster_slot = (
                self.db.query(RosterSlot)
                .filter(
                    RosterSlot.team_id == team_id,
                    RosterSlot.player_id == prev_starter.player_id
                )
                .first()
            )

            if roster_slot:
                roster_slot.is_starter = True
                carried_over = True

        if carried_over:
            self.db.commit()

        return carried_over

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
