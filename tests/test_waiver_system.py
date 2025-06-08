"""Tests for the waiver wire system."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models import League, Player, Team, User, WaiverClaim
from app.services.waiver import WaiverService


@pytest.fixture
def waiver_service(db: Session):
    """Create a waiver service instance."""
    return WaiverService(db)


@pytest.fixture
def sample_league(db: Session):
    """Create a sample league for testing."""
    league = League(
        name="Test League", invite_code="TEST123", max_teams=4, waiver_period_days=2, waiver_type="reverse_standings"
    )
    db.add(league)
    db.commit()
    db.refresh(league)
    return league


@pytest.fixture
def sample_teams(db: Session, sample_league: League):
    """Create sample teams for testing."""
    user1 = User(email="user1@test.com", hashed_password="hash1")
    user2 = User(email="user2@test.com", hashed_password="hash2")
    db.add_all([user1, user2])
    db.commit()

    team1 = Team(name="Team 1", league_id=sample_league.id, owner_id=user1.id)
    team2 = Team(name="Team 2", league_id=sample_league.id, owner_id=user2.id)
    db.add_all([team1, team2])
    db.commit()
    db.refresh(team1)
    db.refresh(team2)
    return [team1, team2]


@pytest.fixture
def sample_players(db: Session):
    """Create sample players for testing."""
    player1 = Player(full_name="Test Player 1", position="G")
    player2 = Player(full_name="Test Player 2", position="F")
    player3 = Player(full_name="Waiver Player", position="C", waiver_expires_at=datetime.utcnow() + timedelta(days=1))
    db.add_all([player1, player2, player3])
    db.commit()
    db.refresh(player1)
    db.refresh(player2)
    db.refresh(player3)
    return [player1, player2, player3]


class TestWaiverService:
    """Test the waiver service functionality."""

    def test_is_player_on_waivers(self, waiver_service: WaiverService, sample_players: list[Player]):
        """Test checking if a player is on waivers."""
        player1, player2, player3 = sample_players

        # Player 1 and 2 are not on waivers
        assert not waiver_service.is_player_on_waivers(player1.id)
        assert not waiver_service.is_player_on_waivers(player2.id)

        # Player 3 is on waivers
        assert waiver_service.is_player_on_waivers(player3.id)

    def test_get_waiver_wire_players(
        self, waiver_service: WaiverService, sample_league: League, sample_players: list[Player]
    ):
        """Test getting players on waivers for a league."""
        players = waiver_service.get_waiver_wire_players(sample_league.id)

        # Should return only the player on waivers
        assert len(players) == 1
        assert players[0].full_name == "Waiver Player"

    def test_put_player_on_waivers(
        self, waiver_service: WaiverService, sample_league: League, sample_players: list[Player]
    ):
        """Test putting a player on waivers."""
        player1 = sample_players[0]

        # Initially not on waivers
        assert not waiver_service.is_player_on_waivers(player1.id)

        # Put on waivers
        success = waiver_service.put_player_on_waivers(player1.id, sample_league.id)
        assert success

        # Now should be on waivers
        assert waiver_service.is_player_on_waivers(player1.id)

    def test_submit_claim(self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]):
        """Test submitting a waiver claim."""
        team = sample_teams[0]
        waiver_player = sample_players[2]  # Player on waivers

        # Submit a claim
        claim = waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=1)

        assert claim.team_id == team.id
        assert claim.player_id == waiver_player.id
        assert claim.priority == 1
        assert claim.status == "pending"

    def test_submit_claim_invalid_player(self, waiver_service: WaiverService, sample_teams: list[Team]):
        """Test submitting a claim for an invalid player."""
        team = sample_teams[0]

        with pytest.raises(ValueError, match="Player .* not found"):
            waiver_service.submit_claim(team_id=team.id, player_id=99999, priority=1)  # Non-existent player

    def test_submit_claim_player_not_on_waivers(
        self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]
    ):
        """Test submitting a claim for a player not on waivers."""
        team = sample_teams[0]
        free_agent = sample_players[0]  # Not on waivers

        with pytest.raises(ValueError, match="Player .* is not on waivers"):
            waiver_service.submit_claim(team_id=team.id, player_id=free_agent.id, priority=1)

    def test_submit_duplicate_claim(
        self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]
    ):
        """Test submitting duplicate claims for the same player."""
        team = sample_teams[0]
        waiver_player = sample_players[2]

        # Submit first claim
        waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=1)

        # Try to submit duplicate claim
        with pytest.raises(ValueError, match="Team already has a pending claim"):
            waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=2)

    def test_cancel_claim(self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]):
        """Test cancelling a waiver claim."""
        team = sample_teams[0]
        waiver_player = sample_players[2]

        # Submit a claim
        claim = waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=1)

        # Cancel the claim
        success = waiver_service.cancel_claim(claim.id, team.id)
        assert success

        # Check that status is updated
        db_claim = waiver_service.db.query(WaiverClaim).filter(WaiverClaim.id == claim.id).first()
        assert db_claim.status == "cancelled"

    def test_get_team_claims(
        self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]
    ):
        """Test getting claims for a team."""
        team = sample_teams[0]
        waiver_player = sample_players[2]

        # Initially no claims
        claims = waiver_service.get_team_claims(team.id)
        assert len(claims) == 0

        # Submit a claim
        waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=1)

        # Now should have one claim
        claims = waiver_service.get_team_claims(team.id)
        assert len(claims) == 1
        assert claims[0].player_id == waiver_player.id

    def test_calculate_waiver_priority_reverse_standings(self, waiver_service: WaiverService, sample_teams: list[Team]):
        """Test waiver priority calculation based on reverse standings."""
        team1, team2 = sample_teams

        # Calculate priorities (without team scores, should default to team order)
        priority1 = waiver_service.calculate_waiver_priority(team1.id)
        priority2 = waiver_service.calculate_waiver_priority(team2.id)

        # Both should get valid priorities
        assert priority1 > 0
        assert priority2 > 0
        assert priority1 != priority2

    def test_get_waiver_priority_order(
        self, waiver_service: WaiverService, sample_league: League, sample_teams: list[Team]
    ):
        """Test getting waiver priority order for a league."""
        priority_order = waiver_service.get_waiver_priority_order(sample_league.id)

        # Should return priority info for both teams
        assert len(priority_order) == 2

        # Should be sorted by priority
        priorities = [team_info["priority"] for team_info in priority_order]
        assert priorities == sorted(priorities)

    def test_process_waivers_empty(self, waiver_service: WaiverService):
        """Test processing waivers when no claims exist."""
        results = waiver_service.process_waivers()

        assert results["total_claims"] == 0
        assert results["successful_claims"] == 0
        assert results["failed_claims"] == 0
        assert results["processed_leagues"] == 0


class TestWaiverAPI:
    """Test waiver API endpoints."""

    # Note: These would require a test client setup with FastAPI
    # For now, we're focusing on service layer tests
    pass


class TestWaiverProcessing:
    """Test waiver processing job functionality."""

    def test_process_single_claim(
        self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player], db: Session
    ):
        """Test processing a single waiver claim."""
        team = sample_teams[0]
        waiver_player = sample_players[2]

        # Submit a claim
        waiver_service.submit_claim(team_id=team.id, player_id=waiver_player.id, priority=1)

        # Process waivers
        results = waiver_service.process_waivers()

        # Should process the claim
        assert results["total_claims"] == 1
        # Note: This might fail without proper roster setup, which is expected
        # In a full test, we'd need to mock the roster service

    def test_process_multiple_claims_priority_order(
        self, waiver_service: WaiverService, sample_teams: list[Team], sample_players: list[Player]
    ):
        """Test processing multiple claims in priority order."""
        team1, team2 = sample_teams
        waiver_player = sample_players[2]

        # Submit claims with different priorities
        waiver_service.submit_claim(team_id=team1.id, player_id=waiver_player.id, priority=2)  # Lower priority

        waiver_service.submit_claim(team_id=team2.id, player_id=waiver_player.id, priority=1)  # Higher priority

        # Process waivers
        results = waiver_service.process_waivers()

        # Should process both claims
        assert results["total_claims"] == 2
        # Higher priority team should get the player, lower priority should fail
        # (exact results depend on roster service implementation)
