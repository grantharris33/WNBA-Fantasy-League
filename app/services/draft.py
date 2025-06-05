from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models import DraftPick, DraftState, League, Player, RosterSlot, Team, TransactionLog, User


class DraftService:
    def __init__(self, db: Session):
        self.db = db

    def start_draft(self, league_id: int, user_id: int) -> DraftState:
        """
        Start a draft for a league.

        Args:
            league_id: The ID of the league
            user_id: The ID of the user initiating the draft (must be commissioner)

        Returns:
            The created DraftState object

        Raises:
            ValueError: If the draft has already started or if user is not the commissioner
        """
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            raise ValueError(f"League with ID {league_id} not found")

        # Check if user is commissioner
        if league.commissioner_id != user_id:
            raise ValueError("Only the commissioner can start the draft")

        # Check if draft already exists
        existing_draft = self.db.query(DraftState).filter(DraftState.league_id == league_id).first()
        if existing_draft:
            if existing_draft.status == "completed":
                raise ValueError("Draft has already been completed")
            if existing_draft.status in ["active", "paused"]:
                raise ValueError("Draft has already started")
            # If draft is pending, we'll reset it
            self.db.delete(existing_draft)
            self.db.commit()

        # Get teams in the league
        teams = self.db.query(Team).filter(Team.league_id == league_id).all()
        if len(teams) < 2 or len(teams) > 4:
            raise ValueError("Draft requires 2-4 teams")

        # Create snake draft order
        team_ids = [team.id for team in teams]
        reverse_team_ids = team_ids.copy()
        reverse_team_ids.reverse()
        pick_order = ",".join(map(str, team_ids + reverse_team_ids))

        # Get timer setting from league settings
        timer_seconds = league.settings.get('draft_timer_seconds', 60) if league.settings else 60

        # Create draft state
        draft_state = DraftState(
            league_id=league_id,
            status="active",
            pick_order=pick_order,
            current_round=1,
            current_pick_index=0,
            seconds_remaining=timer_seconds,
        )

        self.db.add(draft_state)
        self.db.commit()
        self.db.refresh(draft_state)

        # Log the action
        self._log_transaction(user_id, f"Started draft for league {league_id}")

        return draft_state

    def make_pick(
        self, draft_id: int, team_id: int, player_id: int, user_id: int, is_auto: bool = False
    ) -> Tuple[DraftPick, DraftState]:
        """
        Make a draft pick.

        Args:
            draft_id: The ID of the draft
            team_id: The ID of the team making the pick
            player_id: The ID of the player being picked
            user_id: The ID of the user making the pick
            is_auto: Whether this is an auto-pick

        Returns:
            Tuple of (created DraftPick, updated DraftState)

        Raises:
            ValueError: If conditions for a valid pick are not met
        """
        # Get draft state
        draft = self.db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft:
            raise ValueError(f"Draft with ID {draft_id} not found")

        if draft.status != "active":
            raise ValueError(f"Draft is not active (current status: {draft.status})")

        # Check if it's this team's turn
        current_team_id = draft.current_team_id()
        if current_team_id != team_id and not is_auto:
            raise ValueError(f"It's not team {team_id}'s turn to pick")

        # Check if player already drafted
        existing_pick = (
            self.db.query(DraftPick)
            .filter(and_(DraftPick.draft_id == draft_id, DraftPick.player_id == player_id))
            .first()
        )
        if existing_pick:
            raise ValueError(f"Player {player_id} has already been drafted")

        # Get player to check position
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError(f"Player with ID {player_id} not found")

        # Verify roster positional rules are satisfiable
        # This would be a complex check to ensure the team can satisfy the requirement
        # of ≥ 2 G and ≥ 1 F/F-C among starters by the end of draft
        if not self._validate_positional_requirements(team_id, player):
            raise ValueError("This pick would make it impossible to satisfy positional requirements")

        # Calculate pick number
        total_picks = self.db.query(DraftPick).filter(DraftPick.draft_id == draft_id).count()
        pick_number = total_picks + 1

        # Create the pick
        pick = DraftPick(
            draft_id=draft_id,
            team_id=team_id,
            player_id=player_id,
            round=draft.current_round,
            pick_number=pick_number,
            is_auto=is_auto,
        )

        # Add player to team's roster
        roster_slot = RosterSlot(team_id=team_id, player_id=player_id, position=player.position)

        # Get timer setting from league settings
        league = self.db.query(League).filter(League.id == draft.league_id).first()
        timer_seconds = league.settings.get('draft_timer_seconds', 60) if league.settings else 60

        # Update draft state (advance to next pick)
        draft.advance_pick(timer_seconds)

        # Check if draft is complete (10 rounds)
        if draft.current_round > 10:
            draft.status = "completed"
            # Automatically set starters for all teams when draft completes
            self._set_initial_starters_for_all_teams(draft.league_id)

        # Commit changes
        self.db.add(pick)
        self.db.add(roster_slot)
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(pick)
        self.db.refresh(draft)

        # Log the action
        action = f"{'Auto-picked' if is_auto else 'Drafted'} player {player.full_name} for team {team_id}"
        self._log_transaction(user_id, action)

        return pick, draft

    def pause_draft(self, draft_id: int, user_id: int) -> DraftState:
        """
        Pause an active draft.

        Args:
            draft_id: The ID of the draft
            user_id: The ID of the user (must be commissioner)

        Returns:
            Updated DraftState

        Raises:
            ValueError: If draft is not active or user is not commissioner
        """
        draft = self.db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft:
            raise ValueError(f"Draft with ID {draft_id} not found")

        # Check if user is commissioner
        league = self.db.query(League).filter(League.id == draft.league_id).first()
        if league.commissioner_id != user_id:
            raise ValueError("Only the commissioner can pause the draft")

        if draft.status != "active":
            raise ValueError("Draft is not active")

        draft.status = "paused"
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        # Log the action
        self._log_transaction(user_id, f"Paused draft {draft_id}")

        return draft

    def resume_draft(self, draft_id: int, user_id: int) -> DraftState:
        """
        Resume a paused draft.

        Args:
            draft_id: The ID of the draft
            user_id: The ID of the user (must be commissioner)

        Returns:
            Updated DraftState

        Raises:
            ValueError: If draft is not paused or user is not commissioner
        """
        draft = self.db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft:
            raise ValueError(f"Draft with ID {draft_id} not found")

        # Check if user is commissioner
        league = self.db.query(League).filter(League.id == draft.league_id).first()
        if league.commissioner_id != user_id:
            raise ValueError("Only the commissioner can resume the draft")

        if draft.status != "paused":
            raise ValueError("Draft is not paused")

        draft.status = "active"
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        # Log the action
        self._log_transaction(user_id, f"Resumed draft {draft_id}")

        return draft

    def get_draft_state(self, draft_id: int) -> dict:
        """
        Get the current state of a draft.

        Args:
            draft_id: The ID of the draft

        Returns:
            Dictionary with draft state and drafted players
        """
        from sqlalchemy.orm import joinedload

        draft = self.db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft:
            raise ValueError(f"Draft with ID {draft_id} not found")

        # Get all picks in this draft with eager loading of related objects
        picks = (
            self.db.query(DraftPick)
            .options(joinedload(DraftPick.player), joinedload(DraftPick.team))
            .filter(DraftPick.draft_id == draft_id)
            .all()
        )

        # Format picks for response
        formatted_picks = []
        for pick in picks:
            # Access the eager-loaded attributes
            player_name = pick.player.full_name if pick.player else "Unknown"
            player_position = pick.player.position if pick.player else "Unknown"
            team_name = pick.team.name if pick.team else "Unknown"

            formatted_picks.append(
                {
                    "id": pick.id,
                    "round": pick.round,
                    "pick_number": pick.pick_number,
                    "team_id": pick.team_id,
                    "team_name": team_name,
                    "player_id": pick.player_id,
                    "player_name": player_name,
                    "player_position": player_position,
                    "timestamp": pick.timestamp.isoformat(),
                    "is_auto": pick.is_auto,
                }
            )

        # Build response
        response = {**draft.as_dict(), "picks": formatted_picks}

        return response

    def auto_pick(self, draft_id: int) -> Optional[Tuple[DraftPick, DraftState]]:
        """
        Perform an auto-pick for the current team based on best available player by ADP.

        Args:
            draft_id: The ID of the draft

        Returns:
            Tuple of (created DraftPick, updated DraftState) or None if auto-pick not needed
        """
        draft = self.db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft or draft.status != "active":
            return None

        current_team_id = draft.current_team_id()

        # Get best available player (this would ideally use ADP rankings)
        # For now, we'll just pick the first undrafted player
        drafted_player_ids = [
            pick.player_id for pick in self.db.query(DraftPick).filter(DraftPick.draft_id == draft_id).all()
        ]

        best_player = self.db.query(Player).filter(~Player.id.in_(drafted_player_ids)).first()

        if not best_player:
            return None

        # Find system user ID for logging
        system_user = self.db.query(User).filter(User.email == "system@example.com").first()
        system_user_id = system_user.id if system_user else 1  # Default to ID 1 if not found

        # Make the pick
        return self.make_pick(
            draft_id=draft_id, team_id=current_team_id, player_id=best_player.id, user_id=system_user_id, is_auto=True
        )

    def _validate_positional_requirements(self, team_id: int, new_player: Player) -> bool:
        """
        Validate that the team can still satisfy positional requirements after draft.

        Returns:
            True if requirements can be satisfied, False otherwise
        """
        # Get current roster for this team
        current_roster = self.db.query(RosterSlot).filter(RosterSlot.team_id == team_id).all()

        # Count current guards and forwards/centers
        current_guards = sum(1 for slot in current_roster if slot.position.startswith('G'))
        current_forwards = sum(1 for slot in current_roster if 'F' in slot.position or 'C' in slot.position)

        # Check if new player is a guard or forward/centers
        is_guard = new_player.position.startswith('G')
        is_forward = 'F' in new_player.position or 'C' in new_player.position

        # Calculate remaining picks in draft
        draft_id = self.db.query(Team).filter(Team.id == team_id).first().league_id
        draft = self.db.query(DraftState).filter(DraftState.league_id == draft_id).first()

        total_rounds = 10  # Standard draft length
        current_round = draft.current_round
        remaining_picks = total_rounds - current_round + (1 if draft.current_team_id() == team_id else 0)

        # We need at least 2 guards and 1 forward/center
        guards_needed = max(0, 2 - current_guards - (1 if is_guard else 0))
        forwards_needed = max(0, 1 - current_forwards - (1 if is_forward else 0))

        # Check if we can satisfy requirements with remaining picks
        return remaining_picks >= (guards_needed + forwards_needed)

    def _set_initial_starters_for_all_teams(self, league_id: int) -> None:
        """
        Automatically set starters for all teams in a league after draft completion.
        Selects the first 5 players that satisfy positional requirements (>=2G, >=1F/C).
        """
        # Get all teams in the league
        teams = self.db.query(Team).filter(Team.league_id == league_id).all()

        for team in teams:
            self._set_initial_starters_for_team(team.id)

    def _set_initial_starters_for_team(self, team_id: int) -> None:
        """
        Set initial starters for a single team based on draft order and position requirements.
        """
        # Get all roster slots for this team, ordered by draft pick order
        roster_slots = (
            self.db.query(RosterSlot)
            .join(DraftPick, RosterSlot.player_id == DraftPick.player_id)
            .filter(RosterSlot.team_id == team_id)
            .order_by(DraftPick.pick_number)
            .all()
        )

        if len(roster_slots) < 5:
            # Team doesn't have enough players to set starters
            return

        # Try to find the first valid 5-player combination that meets position requirements
        selected_starters = self._find_valid_starter_combination(roster_slots)

        if len(selected_starters) == 5:
            # Set the selected players as starters
            for slot in roster_slots:
                if slot.player_id in selected_starters:
                    slot.is_starter = True
                else:
                    slot.is_starter = False

            # Log the action
            player_names = []
            for slot in roster_slots:
                if slot.is_starter:
                    player = self.db.query(Player).filter(Player.id == slot.player_id).first()
                    player_names.append(player.full_name if player else "Unknown")

            team = self.db.query(Team).filter(Team.id == team_id).first()
            action = f"Auto-set initial starters for {team.name if team else 'Unknown Team'}: {', '.join(player_names)}"
            self._log_transaction(None, action)  # No specific user for auto-action

    def _find_valid_starter_combination(self, roster_slots: List[RosterSlot]) -> List[int]:
        """
        Find the first valid combination of 5 players that meets position requirements.
        Returns list of player IDs.
        """
        from itertools import combinations

        # Get player positions for all roster slots
        player_positions = {}
        for slot in roster_slots:
            player = self.db.query(Player).filter(Player.id == slot.player_id).first()
            player_positions[slot.player_id] = player.position if player else None

        # Try combinations starting with the first drafted players (prioritize early picks)
        # First try combinations that include the first 3 picks, then expand
        roster_player_ids = [slot.player_id for slot in roster_slots]

        # Start with combinations that include early picks, then try all combinations
        for start_index in range(min(3, len(roster_slots) - 4)):  # Start with first few picks
            for combo in combinations(roster_player_ids[start_index:], 5):
                if self._validate_starter_positions(combo, player_positions):
                    return list(combo)

        # If no valid combination found with early picks, try all combinations
        for combo in combinations(roster_player_ids, 5):
            if self._validate_starter_positions(combo, player_positions):
                return list(combo)

        # If no valid combination found, just take first 5 players
        return roster_player_ids[:5]

    def _validate_starter_positions(self, player_ids: tuple, player_positions: dict) -> bool:
        """
        Validate that a combination of players meets position requirements.
        Returns True if the combination has >=2 Guards and >=1 Forward/Center.
        """
        positions = [player_positions.get(pid) for pid in player_ids if player_positions.get(pid)]

        guard_count = sum(1 for pos in positions if pos and 'G' in pos)
        forward_center_count = sum(1 for pos in positions if pos and ('F' in pos or 'C' in pos))

        return guard_count >= 2 and forward_center_count >= 1

    def _log_transaction(self, user_id: int, action: str) -> None:
        """Log a transaction to the transaction_log table."""
        log_entry = TransactionLog(user_id=user_id, action=action)
        self.db.add(log_entry)
        self.db.commit()
