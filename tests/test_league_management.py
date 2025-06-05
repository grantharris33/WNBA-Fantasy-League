"""Tests for league management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import DraftState, League, Team, User
from app.services.league import LeagueService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(email="test@example.com", hashed_password="hashed_password", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user2(db: Session):
    """Create a second test user."""
    user = User(email="test2@example.com", hashed_password="hashed_password", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def league_service(db: Session):
    """League service fixture."""
    return LeagueService(db)


class TestLeagueService:
    """Test the LeagueService class."""

    def test_generate_invite_code(self, league_service):
        """Test invite code generation."""
        code = league_service.generate_invite_code()
        assert code.startswith("LEAGUE-")
        assert len(code) == 16  # LEAGUE-XXXX-XXXX
        assert code[6] == "-"
        assert code[11] == "-"

    def test_create_league(self, league_service, test_user):
        """Test league creation."""
        league = league_service.create_league(name="Test League", commissioner=test_user, max_teams=8)

        assert league.name == "Test League"
        assert league.commissioner_id == test_user.id
        assert league.max_teams == 8
        assert league.is_active is True
        assert league.invite_code is not None
        assert league.invite_code.startswith("LEAGUE-")

    def test_create_league_invalid_max_teams(self, league_service, test_user):
        """Test league creation with invalid max_teams."""
        with pytest.raises(Exception) as exc_info:
            league_service.create_league(name="Test League", commissioner=test_user, max_teams=1)  # Too low
        assert "max_teams must be between 2 and 12" in str(exc_info.value.detail)

        with pytest.raises(Exception) as exc_info:
            league_service.create_league(name="Test League", commissioner=test_user, max_teams=13)  # Too high
        assert "max_teams must be between 2 and 12" in str(exc_info.value.detail)

    def test_join_league(self, league_service, test_user, test_user2):
        """Test joining a league."""
        # Create league
        league = league_service.create_league(name="Test League", commissioner=test_user)

        # Join league
        team = league_service.join_league(invite_code=league.invite_code, team_name="Test Team", user=test_user2)

        assert team.name == "Test Team"
        assert team.owner_id == test_user2.id
        assert team.league_id == league.id

    def test_join_league_invalid_code(self, league_service, test_user):
        """Test joining with invalid invite code."""
        with pytest.raises(Exception) as exc_info:
            league_service.join_league(invite_code="INVALID-CODE", team_name="Test Team", user=test_user)
        assert "Invalid or expired invite code" in str(exc_info.value.detail)

    def test_join_league_duplicate_user(self, league_service, test_user, test_user2):
        """Test user trying to join same league twice."""
        # Create league and join once
        league = league_service.create_league(name="Test League", commissioner=test_user)

        league_service.join_league(invite_code=league.invite_code, team_name="Test Team", user=test_user2)

        # Try to join again
        with pytest.raises(Exception) as exc_info:
            league_service.join_league(invite_code=league.invite_code, team_name="Test Team 2", user=test_user2)
        assert "You already have a team in this league" in str(exc_info.value.detail)

    def test_join_league_duplicate_team_name(self, league_service, test_user, test_user2, db):
        """Test duplicate team name in same league."""
        # Create league and join once
        league = league_service.create_league(name="Test League", commissioner=test_user)

        league_service.join_league(invite_code=league.invite_code, team_name="Test Team", user=test_user2)

        # Create another user
        user3 = User(email="test3@example.com", hashed_password="hashed_password")
        db.add(user3)
        db.commit()
        db.refresh(user3)

        # Try to join with same team name
        with pytest.raises(Exception) as exc_info:
            league_service.join_league(invite_code=league.invite_code, team_name="Test Team", user=user3)  # Same name
        assert "Team name already taken in this league" in str(exc_info.value.detail)

    def test_join_league_full(self, league_service, test_user, db):
        """Test joining a full league."""
        # Create league with max 2 teams
        league = league_service.create_league(name="Test League", commissioner=test_user, max_teams=2)

        # Create and add 2 users
        for i in range(2):
            user = User(email=f"user{i}@example.com", hashed_password="hashed_password")
            db.add(user)
            db.commit()
            db.refresh(user)

            league_service.join_league(invite_code=league.invite_code, team_name=f"Team {i}", user=user)

        # Try to add third user
        user3 = User(email="user3@example.com", hashed_password="hashed_password")
        db.add(user3)
        db.commit()
        db.refresh(user3)

        with pytest.raises(Exception) as exc_info:
            league_service.join_league(invite_code=league.invite_code, team_name="Team 3", user=user3)
        assert "League has reached maximum capacity" in str(exc_info.value.detail)

    def test_update_league_non_commissioner(self, league_service, test_user, test_user2):
        """Test non-commissioner trying to update league."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        with pytest.raises(Exception) as exc_info:
            league_service.update_league(
                league_id=league.id, user=test_user2, name="Updated League"  # Not commissioner
            )
        assert "Only the commissioner can perform this action" in str(exc_info.value.detail)

    def test_update_league_after_draft_starts(self, league_service, test_user, db):
        """Test updating league after draft starts."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        # Create draft state
        draft_state = DraftState(league_id=league.id, status="active", pick_order="1,2")
        db.add(draft_state)
        db.commit()

        with pytest.raises(Exception) as exc_info:
            league_service.update_league(league_id=league.id, user=test_user, name="Updated League")
        assert "Cannot modify league after draft starts" in str(exc_info.value.detail)

    def test_delete_league_non_commissioner(self, league_service, test_user, test_user2):
        """Test non-commissioner trying to delete league."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        with pytest.raises(Exception) as exc_info:
            league_service.delete_league(league_id=league.id, user=test_user2)  # Not commissioner
        assert "Only the commissioner can perform this action" in str(exc_info.value.detail)

    def test_delete_league_after_draft_starts(self, league_service, test_user, db):
        """Test deleting league after draft starts."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        # Create draft state
        draft_state = DraftState(league_id=league.id, status="active", pick_order="1,2")
        db.add(draft_state)
        db.commit()

        with pytest.raises(Exception) as exc_info:
            league_service.delete_league(league_id=league.id, user=test_user)
        assert "Cannot delete league after draft starts" in str(exc_info.value.detail)

    def test_leave_league_after_draft_starts(self, league_service, test_user, test_user2, db):
        """Test leaving league after draft starts."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        team = league_service.join_league(invite_code=league.invite_code, team_name="Test Team", user=test_user2)

        # Create draft state
        draft_state = DraftState(league_id=league.id, status="active", pick_order="1,2")
        db.add(draft_state)
        db.commit()

        with pytest.raises(Exception) as exc_info:
            league_service.leave_league(league_id=league.id, team_id=team.id, user=test_user2)
        assert "Cannot leave league after draft starts" in str(exc_info.value.detail)

    def test_generate_new_invite_code(self, league_service, test_user):
        """Test generating new invite code."""
        league = league_service.create_league(name="Test League", commissioner=test_user)

        old_code = league.invite_code
        new_code = league_service.generate_new_invite_code(league_id=league.id, user=test_user)

        assert new_code != old_code
        assert new_code.startswith("LEAGUE-")

    def test_get_user_leagues(self, league_service, test_user, test_user2):
        """Test getting user's leagues."""
        # Create league as commissioner
        league1 = league_service.create_league(name="Owned League", commissioner=test_user)

        # Create another league and join as member
        league2 = league_service.create_league(name="Member League", commissioner=test_user2)

        league_service.join_league(invite_code=league2.invite_code, team_name="Test Team", user=test_user)

        # Get user leagues
        user_leagues = league_service.get_user_leagues(user=test_user)

        assert len(user_leagues) == 2

        # Check roles
        roles = {item["league"].id: item["role"] for item in user_leagues}
        assert roles[league1.id] == "commissioner"
        assert roles[league2.id] == "member"
