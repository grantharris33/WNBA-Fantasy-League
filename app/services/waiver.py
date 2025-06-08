"""Waiver wire service for managing waiver claims and processing."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import League, Player, RosterSlot, Team, TeamScore, WaiverClaim


class WaiverService:
    """Service for handling waiver wire operations."""

    def __init__(self, db: Session):
        self.db = db

    def submit_claim(
        self, team_id: int, player_id: int, drop_player_id: int | None = None, priority: int | None = None
    ) -> WaiverClaim:
        """Submit a waiver claim for a player.

        Args:
            team_id: ID of the team making the claim
            player_id: ID of the player being claimed
            drop_player_id: Optional ID of player to drop for roster space
            priority: Optional priority (if None, calculates automatically)

        Returns:
            Created WaiverClaim instance

        Raises:
            ValueError: If claim is invalid
        """
        # Validate team exists
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # Validate player exists and is on waivers
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise ValueError(f"Player {player_id} not found")

        if not self.is_player_on_waivers(player_id):
            raise ValueError(f"Player {player_id} is not on waivers")

        # Check if team already has a pending claim for this player
        existing_claim = (
            self.db.query(WaiverClaim)
            .filter(
                and_(
                    WaiverClaim.team_id == team_id, WaiverClaim.player_id == player_id, WaiverClaim.status == "pending"
                )
            )
            .first()
        )
        if existing_claim:
            raise ValueError("Team already has a pending claim for this player")

        # Validate drop player if specified
        if drop_player_id:
            drop_player = self.db.query(Player).filter(Player.id == drop_player_id).first()
            if not drop_player:
                raise ValueError(f"Drop player {drop_player_id} not found")

            # Check that drop player is on the team's roster
            roster_slot = (
                self.db.query(RosterSlot)
                .filter(and_(RosterSlot.team_id == team_id, RosterSlot.player_id == drop_player_id))
                .first()
            )
            if not roster_slot:
                raise ValueError("Drop player is not on team's roster")

        # Calculate priority if not provided
        if priority is None:
            priority = self.calculate_waiver_priority(team_id)

        # Create the claim
        claim = WaiverClaim(
            team_id=team_id, player_id=player_id, drop_player_id=drop_player_id, priority=priority, status="pending"
        )

        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)

        return claim

    def cancel_claim(self, claim_id: int, team_id: int) -> bool:
        """Cancel a pending waiver claim.

        Args:
            claim_id: ID of the claim to cancel
            team_id: ID of the team (for authorization)

        Returns:
            True if cancelled successfully

        Raises:
            ValueError: If claim not found or not cancellable
        """
        claim = (
            self.db.query(WaiverClaim)
            .filter(and_(WaiverClaim.id == claim_id, WaiverClaim.team_id == team_id, WaiverClaim.status == "pending"))
            .first()
        )

        if not claim:
            raise ValueError("Claim not found or not cancellable")

        claim.status = "cancelled"
        self.db.commit()

        return True

    def get_team_claims(self, team_id: int) -> list[WaiverClaim]:
        """Get all waiver claims for a team.

        Args:
            team_id: ID of the team

        Returns:
            List of waiver claims
        """
        return (
            self.db.query(WaiverClaim)
            .options(joinedload(WaiverClaim.player), joinedload(WaiverClaim.drop_player))
            .filter(WaiverClaim.team_id == team_id)
            .order_by(desc(WaiverClaim.created_at))
            .all()
        )

    def get_waiver_wire_players(self, league_id: int) -> list[Player]:
        """Get all players currently on waivers for a league.

        Args:
            league_id: ID of the league

        Returns:
            List of players on waivers
        """
        now = datetime.utcnow()

        return (
            self.db.query(Player)
            .filter(
                and_(
                    Player.waiver_expires_at.isnot(None),
                    Player.waiver_expires_at > now,
                    Player.team_id.is_(None),  # Not on any fantasy team
                )
            )
            .order_by(Player.waiver_expires_at)
            .all()
        )

    def is_player_on_waivers(self, player_id: int) -> bool:
        """Check if a player is currently on waivers.

        Args:
            player_id: ID of the player

        Returns:
            True if player is on waivers
        """
        now = datetime.utcnow()
        player = self.db.query(Player).filter(Player.id == player_id).first()

        if not player:
            return False

        return player.waiver_expires_at is not None and player.waiver_expires_at > now and player.team_id is None

    def calculate_waiver_priority(self, team_id: int) -> int:
        """Calculate waiver priority for a team.

        Args:
            team_id: ID of the team

        Returns:
            Priority number (1 = highest priority)
        """
        # Get team and league
        team = self.db.query(Team).options(joinedload(Team.league)).filter(Team.id == team_id).first()

        if not team or not team.league:
            raise ValueError("Team or league not found")

        league = team.league

        if league.waiver_type == "reverse_standings":
            return self._calculate_reverse_standings_priority(team_id, league.id)
        elif league.waiver_type == "continual_rolling":
            return self._calculate_rolling_priority(team_id, league.id)
        else:
            # Default to reverse standings
            return self._calculate_reverse_standings_priority(team_id, league.id)

    def _calculate_reverse_standings_priority(self, team_id: int, league_id: int) -> int:
        """Calculate priority based on reverse standings (worst team gets #1 priority)."""
        # Get current week (simplified - could be more sophisticated)
        self._get_current_week()

        # Get team standings based on total points
        team_standings = (
            self.db.query(Team.id, func.coalesce(func.sum(TeamScore.score), 0).label("total_score"))
            .outerjoin(TeamScore)
            .filter(Team.league_id == league_id)
            .group_by(Team.id)
            .order_by("total_score")  # Ascending order (worst first)
            .all()
        )

        # Find team's position in standings (1-indexed)
        for i, (standing_team_id, _) in enumerate(team_standings):
            if standing_team_id == team_id:
                return i + 1

        return len(team_standings)  # Default to last

    def _calculate_rolling_priority(self, team_id: int, league_id: int) -> int:
        """Calculate priority based on continual rolling (moves to end after successful claim)."""
        # For now, implement as reverse standings
        # In a full implementation, you'd track successful claims and reorder
        return self._calculate_reverse_standings_priority(team_id, league_id)

    def _get_current_week(self) -> int:
        """Get the current fantasy week. Simplified implementation."""
        # This could be more sophisticated based on league settings
        # For now, assume week 1 starts on a certain date
        return 1

    def process_waivers(self, league_id: int | None = None) -> dict[str, Any]:
        """Process all pending waiver claims.

        Args:
            league_id: Optional league ID to process only specific league

        Returns:
            Dictionary with processing results
        """
        results = {"total_claims": 0, "successful_claims": 0, "failed_claims": 0, "processed_leagues": 0, "errors": []}

        try:
            # Get all pending claims
            query = (
                self.db.query(WaiverClaim)
                .options(
                    joinedload(WaiverClaim.team).joinedload(Team.league),
                    joinedload(WaiverClaim.player),
                    joinedload(WaiverClaim.drop_player),
                )
                .filter(WaiverClaim.status == "pending")
            )

            if league_id:
                query = query.join(Team).filter(Team.league_id == league_id)

            pending_claims = query.all()
            results["total_claims"] = len(pending_claims)

            # Group claims by league for processing
            league_claims = {}
            for claim in pending_claims:
                league_id = claim.team.league_id
                if league_id not in league_claims:
                    league_claims[league_id] = []
                league_claims[league_id].append(claim)

            # Process each league's claims
            for league_id, claims in league_claims.items():
                try:
                    league_results = self._process_league_waivers(league_id, claims)
                    results["successful_claims"] += league_results["successful"]
                    results["failed_claims"] += league_results["failed"]
                    results["errors"].extend(league_results["errors"])
                    results["processed_leagues"] += 1
                except Exception as e:
                    results["errors"].append(f"Error processing league {league_id}: {str(e)}")

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            results["errors"].append(f"Fatal error during waiver processing: {str(e)}")

        return results

    def _process_league_waivers(self, league_id: int, claims: list[WaiverClaim]) -> dict[str, Any]:
        """Process waiver claims for a specific league."""
        results = {"successful": 0, "failed": 0, "errors": []}

        # Group claims by player
        player_claims = {}
        for claim in claims:
            player_id = claim.player_id
            if player_id not in player_claims:
                player_claims[player_id] = []
            player_claims[player_id].append(claim)

        # Process each player's claims
        for player_id, player_claims_list in player_claims.items():
            try:
                # Sort by priority (1 = highest priority)
                player_claims_list.sort(key=lambda c: c.priority)

                # Try to award the player to the highest priority team
                awarded = False
                for claim in player_claims_list:
                    if awarded:
                        # Mark remaining claims as failed
                        claim.status = "failed"
                        claim.processed_at = datetime.utcnow()
                        results["failed"] += 1
                        continue

                    try:
                        # Check if player is still available
                        if not self.is_player_on_waivers(player_id):
                            claim.status = "failed"
                            claim.processed_at = datetime.utcnow()
                            results["failed"] += 1
                            continue

                        # Check roster space and process the claim
                        success = self._process_individual_claim(claim)
                        if success:
                            claim.status = "successful"
                            claim.processed_at = datetime.utcnow()
                            results["successful"] += 1
                            awarded = True
                        else:
                            claim.status = "failed"
                            claim.processed_at = datetime.utcnow()
                            results["failed"] += 1

                    except Exception as e:
                        claim.status = "failed"
                        claim.processed_at = datetime.utcnow()
                        results["failed"] += 1
                        results["errors"].append(f"Error processing claim {claim.id}: {str(e)}")

            except Exception as e:
                results["errors"].append(f"Error processing player {player_id} claims: {str(e)}")

        return results

    def _process_individual_claim(self, claim: WaiverClaim) -> bool:
        """Process an individual waiver claim.

        Args:
            claim: The waiver claim to process

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.services.roster import RosterService

            roster_service = RosterService(self.db)

            # Handle roster drop if specified
            if claim.drop_player_id:
                # Remove player from roster (this should also put them on waivers)
                success = roster_service.drop_player(claim.team_id, claim.drop_player_id)
                if not success:
                    return False

            # Add claimed player to roster
            success = roster_service.add_player(claim.team_id, claim.player_id)
            if not success:
                return False

            # Clear waiver status from player
            player = self.db.query(Player).filter(Player.id == claim.player_id).first()
            if player:
                player.waiver_expires_at = None
                player.team_id = claim.team_id

            return True

        except Exception:
            return False

    def put_player_on_waivers(self, player_id: int, league_id: int) -> bool:
        """Put a player on waivers for the specified period.

        Args:
            player_id: ID of the player
            league_id: ID of the league (for waiver period settings)

        Returns:
            True if successful
        """
        # Get league waiver settings
        league = self.db.query(League).filter(League.id == league_id).first()
        if not league:
            return False

        # Calculate waiver expiration
        waiver_expires_at = datetime.utcnow() + timedelta(days=league.waiver_period_days)

        # Update player
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return False

        player.waiver_expires_at = waiver_expires_at
        player.team_id = None  # Remove from fantasy team

        self.db.commit()
        return True

    def get_waiver_priority_order(self, league_id: int) -> list[dict[str, Any]]:
        """Get the waiver priority order for all teams in a league.

        Args:
            league_id: ID of the league

        Returns:
            List of team info with priority order
        """
        teams = self.db.query(Team).filter(Team.league_id == league_id).all()

        team_priorities = []
        for team in teams:
            priority = self.calculate_waiver_priority(team.id)
            team_priorities.append({"team_id": team.id, "team_name": team.name, "priority": priority})

        # Sort by priority (1 = highest)
        team_priorities.sort(key=lambda x: x["priority"])
        return team_priorities
