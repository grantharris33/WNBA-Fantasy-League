"""Tests for admin API endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Team, WeeklyLineup, TeamScore, Player, RosterSlot
from app.core.security import hash_password, create_access_token
from app.main import app


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user for testing."""
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("password"),
        is_admin=True
    )
    db.add(admin)
    db.commit()
    return admin


@pytest.fixture
def regular_user(db: Session):
    """Create a regular user for testing."""
    user = User(
        email="user@test.com",
        hashed_password=hash_password("password"),
        is_admin=False
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin_token(admin_user: User):
    """Create an access token for the admin user."""
    return create_access_token(subject=admin_user.id)


@pytest.fixture
def regular_token(regular_user: User):
    """Create an access token for the regular user."""
    return create_access_token(subject=regular_user.id)


@pytest.fixture
def test_team(db: Session, regular_user: User):
    """Create a test team."""
    team = Team(
        name="Test Team",
        owner_id=regular_user.id,
        league_id=1,
        moves_this_week=3
    )
    db.add(team)
    db.commit()
    return team


@pytest.fixture
def test_players(db: Session):
    """Create test players."""
    players = []
    for i in range(10):
        player = Player(
            full_name=f"Player {i}",
            position="G" if i < 5 else "F",
            team_abbr="TEST",
            status="active"
        )
        db.add(player)
        players.append(player)

    db.commit()
    return players


@pytest.fixture
def test_weekly_lineup(db: Session, test_team: Team, test_players: list):
    """Create a test weekly lineup."""
    week_id = 202501
    lineup_entries = []

    for i, player in enumerate(test_players[:8]):  # 8 players on roster
        is_starter = i < 5  # First 5 are starters

        # Add to roster
        roster_slot = RosterSlot(
            team_id=test_team.id,
            player_id=player.id,
            position=player.position,
            is_starter=is_starter
        )
        db.add(roster_slot)

        # Add to weekly lineup
        lineup_entry = WeeklyLineup(
            team_id=test_team.id,
            player_id=player.id,
            week_id=week_id,
            is_starter=is_starter,
            locked_at=datetime.utcnow()
        )
        db.add(lineup_entry)
        lineup_entries.append(lineup_entry)

    db.commit()
    return lineup_entries


class TestAdminAPI:
    """Test cases for admin API endpoints."""

    def test_modify_historical_lineup_success(self, client: TestClient, admin_token: str, test_team: Team, test_weekly_lineup: list, test_players: list):
        """Test successful historical lineup modification."""
        new_starter_ids = [p.id for p in test_players[2:7]]  # Different 5 players

        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            json={
                "starter_ids": new_starter_ids,
                "justification": "Testing lineup modification"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully modified lineup" in data["message"]
        assert data["data"]["team_id"] == test_team.id
        assert data["data"]["week_id"] == 202501
        assert data["data"]["starter_ids"] == new_starter_ids

    def test_modify_historical_lineup_unauthorized(self, client: TestClient, regular_token: str, test_team: Team):
        """Test lineup modification without admin privileges."""
        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            json={
                "starter_ids": [1, 2, 3, 4, 5],
                "justification": "Testing"
            },
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_modify_historical_lineup_no_auth(self, client: TestClient, test_team: Team):
        """Test lineup modification without authentication."""
        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            json={
                "starter_ids": [1, 2, 3, 4, 5],
                "justification": "Testing"
            }
        )

        assert response.status_code == 401

    def test_modify_historical_lineup_invalid_team(self, client: TestClient, admin_token: str):
        """Test lineup modification with invalid team ID."""
        response = client.put(
            "/api/v1/admin/teams/999/lineups/202501",
            json={
                "starter_ids": [1, 2, 3, 4, 5],
                "justification": "Testing"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "Team with ID 999 not found" in response.json()["detail"]

    def test_modify_historical_lineup_wrong_starter_count(self, client: TestClient, admin_token: str, test_team: Team, test_weekly_lineup: list):
        """Test lineup modification with wrong number of starters."""
        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            json={
                "starter_ids": [1, 2, 3],  # Only 3 starters
                "justification": "Testing"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "Must specify exactly 5 starters" in response.json()["detail"]

    def test_recalculate_score_success(self, client: TestClient, admin_token: str, test_team: Team):
        """Test successful score recalculation."""
        # Create a team score first
        response = client.post(
            f"/api/v1/admin/teams/{test_team.id}/weeks/202501/recalculate",
            json={"justification": "Testing score recalculation"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully recalculated score" in data["message"]

    def test_recalculate_score_unauthorized(self, client: TestClient, regular_token: str, test_team: Team):
        """Test score recalculation without admin privileges."""
        response = client.post(
            f"/api/v1/admin/teams/{test_team.id}/weeks/202501/recalculate",
            json={"justification": "Testing"},
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403

    def test_grant_additional_moves_success(self, client: TestClient, admin_token: str, test_team: Team):
        """Test successful granting of additional moves."""
        response = client.post(
            f"/api/v1/admin/teams/{test_team.id}/moves/grant",
            json={
                "additional_moves": 2,
                "justification": "Testing move grant"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully granted 2 additional moves" in data["message"]
        assert data["data"]["additional_moves"] == 2

    def test_grant_additional_moves_unauthorized(self, client: TestClient, regular_token: str, test_team: Team):
        """Test granting moves without admin privileges."""
        response = client.post(
            f"/api/v1/admin/teams/{test_team.id}/moves/grant",
            json={
                "additional_moves": 2,
                "justification": "Testing"
            },
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403

    def test_grant_additional_moves_invalid_team(self, client: TestClient, admin_token: str):
        """Test granting moves with invalid team ID."""
        response = client.post(
            "/api/v1/admin/teams/999/moves/grant",
            json={
                "additional_moves": 2,
                "justification": "Testing"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "Team with ID 999 not found" in response.json()["detail"]

    def test_get_audit_log_success(self, client: TestClient, admin_token: str):
        """Test successful audit log retrieval."""
        response = client.get(
            "/api/v1/admin/audit-log",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_log_with_filters(self, client: TestClient, admin_token: str, test_team: Team):
        """Test audit log retrieval with filters."""
        response = client.get(
            f"/api/v1/admin/audit-log?team_id={test_team.id}&limit=50&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_log_unauthorized(self, client: TestClient, regular_token: str):
        """Test audit log retrieval without admin privileges."""
        response = client.get(
            "/api/v1/admin/audit-log",
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403

    def test_get_team_lineup_history_success(self, client: TestClient, admin_token: str, test_team: Team, test_weekly_lineup: list):
        """Test successful team lineup history retrieval."""
        response = client.get(
            f"/api/v1/admin/teams/{test_team.id}/lineup-history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_team_lineup_history_unauthorized(self, client: TestClient, regular_token: str, test_team: Team):
        """Test lineup history retrieval without admin privileges."""
        response = client.get(
            f"/api/v1/admin/teams/{test_team.id}/lineup-history",
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403

    def test_get_admin_lineup_view_success(self, client: TestClient, admin_token: str, test_team: Team, test_weekly_lineup: list):
        """Test successful admin lineup view retrieval."""
        response = client.get(
            f"/api/v1/admin/teams/{test_team.id}/weeks/202501/lineup",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == test_team.id
        assert data["week_id"] == 202501
        assert "lineup" in data
        assert "admin_modified" in data

    def test_get_admin_lineup_view_not_found(self, client: TestClient, admin_token: str):
        """Test getting lineup view for non-existent team/week returns 404."""
        response = client.get(
            "/api/v1/admin/teams/999/weeks/1/lineup",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_get_admin_lineup_view_unauthorized(self, client: TestClient, regular_token: str, test_team: Team):
        """Test admin lineup view without admin privileges."""
        response = client.get(
            f"/api/v1/admin/teams/{test_team.id}/weeks/202501/lineup",
            headers={"Authorization": f"Bearer {regular_token}"}
        )

        assert response.status_code == 403

    def test_admin_endpoints_require_valid_json(self, client: TestClient, admin_token: str, test_team: Team):
        """Test that admin endpoints require valid JSON payloads."""
        # Test modify lineup with invalid JSON
        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            data="invalid json",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 422

    def test_admin_endpoints_validate_request_schemas(self, client: TestClient, admin_token: str, test_team: Team):
        """Test that admin endpoints validate request schemas."""
        # Test modify lineup with missing required field
        response = client.put(
            f"/api/v1/admin/teams/{test_team.id}/lineups/202501",
            json={"justification": "test"},  # Missing starter_ids
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422

        # Test grant moves with invalid data type
        response = client.post(
            f"/api/v1/admin/teams/{test_team.id}/moves/grant",
            json={
                "additional_moves": "not_a_number",
                "justification": "test"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422

    # Tests for Story 3: Enhanced Admin Move Management

    def test_grant_team_moves_success(self, client: TestClient, admin_token: str, db: Session):
        """Test successfully granting moves to a team."""
        # Create test data
        from app.models import Team, League, User

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id)
        db.add(team)
        db.flush()

        # Grant moves
        response = client.post(
            f"/api/v1/admin/teams/{team.id}/weeks/1/grant-moves",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "moves_to_grant": 2,
                "reason": "Emergency injury replacement",
                "week_id": 1
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == team.id
        assert data["moves_granted"] == 2
        assert data["reason"] == "Emergency injury replacement"
        assert data["week_id"] == 1

    def test_grant_team_moves_invalid_team(self, client: TestClient, admin_token: str):
        """Test granting moves to non-existent team returns 400."""
        response = client.post(
            "/api/v1/admin/teams/999/weeks/1/grant-moves",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "moves_to_grant": 2,
                "reason": "Test",
                "week_id": 1
            }
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_grant_team_moves_invalid_input(self, client: TestClient, admin_token: str, db: Session):
        """Test granting moves with invalid input returns 400."""
        # Create test data
        from app.models import Team, League

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id)
        db.add(team)
        db.flush()

        # Test zero moves
        response = client.post(
            f"/api/v1/admin/teams/{team.id}/weeks/1/grant-moves",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "moves_to_grant": 0,
                "reason": "Test",
                "week_id": 1
            }
        )

        assert response.status_code == 400
        assert "Must grant at least 1 move" in response.json()["detail"]

    def test_get_team_move_summary_success(self, client: TestClient, admin_token: str, db: Session):
        """Test getting team move summary."""
        # Create test data
        from app.models import Team, League, User, AdminMoveGrant

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id, moves_this_week=1)
        db.add(team)
        db.flush()

        # Create admin user for the grant
        admin_user = User(email="admin_grant@test.com", hashed_password="hashed", is_admin=True)
        db.add(admin_user)
        db.flush()

        # Add admin grant
        grant = AdminMoveGrant(
            team_id=team.id,
            admin_user_id=admin_user.id,
            moves_granted=2,
            reason="Emergency",
            week_id=1
        )
        db.add(grant)
        db.commit()

        # Get summary
        response = client.get(
            f"/api/v1/admin/teams/{team.id}/weeks/1/move-summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == team.id
        assert data["week_id"] == 1
        assert data["base_moves"] == 3
        assert data["admin_granted_moves"] == 2
        assert data["total_available_moves"] == 5
        assert data["moves_used"] == 1
        assert data["moves_remaining"] == 4
        assert len(data["admin_grants"]) == 1

    def test_get_team_move_summary_invalid_team(self, client: TestClient, admin_token: str):
        """Test getting move summary for non-existent team returns 400."""
        response = client.get(
            "/api/v1/admin/teams/999/weeks/1/move-summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_force_set_team_roster_success(self, client: TestClient, admin_token: str, db: Session):
        """Test force setting team roster with admin override."""
        # Create test data
        from app.models import Team, League, Player, RosterSlot

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id, moves_this_week=3)  # At limit
        db.add(team)
        db.flush()

        # Create players
        players = []
        for i in range(7):
            position = "G" if i < 2 else ("F" if i < 4 else "C")
            player = Player(full_name=f"Player {i+1}", position=position)
            db.add(player)
            players.append(player)

        db.flush()

        # Add players to roster
        for i, player in enumerate(players):
            is_starter = i < 5
            slot = RosterSlot(
                team_id=team.id,
                player_id=player.id,
                position=player.position,
                is_starter=is_starter
            )
            db.add(slot)

        db.commit()

        # Force set roster (change one starter)
        new_starter_ids = [players[0].id, players[1].id, players[2].id, players[5].id, players[4].id]

        response = client.put(
            f"/api/v1/admin/teams/{team.id}/weeks/1/force-roster",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "starter_ids": new_starter_ids,
                "week_id": 1,
                "bypass_move_limit": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["team_id"] == team.id
        assert data["data"]["week_id"] == 1
        assert data["data"]["bypass_move_limit"] is True

    def test_force_set_team_roster_invalid_positions(self, client: TestClient, admin_token: str, db: Session):
        """Test force setting roster with invalid positions returns 400."""
        # Create test data
        from app.models import Team, League, Player, RosterSlot

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id)
        db.add(team)
        db.flush()

        # Create players (all forwards - invalid lineup)
        players = []
        for i in range(5):
            player = Player(full_name=f"Player {i+1}", position="F")
            db.add(player)
            players.append(player)

        db.flush()

        # Add players to roster
        for player in players:
            slot = RosterSlot(
                team_id=team.id,
                player_id=player.id,
                position=player.position,
                is_starter=False
            )
            db.add(slot)

        db.commit()

        # Try to force set invalid roster
        response = client.put(
            f"/api/v1/admin/teams/{team.id}/weeks/1/force-roster",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "starter_ids": [p.id for p in players],
                "week_id": 1,
                "bypass_move_limit": True
            }
        )

        assert response.status_code == 400
        assert "at least 2 players with Guard" in response.json()["detail"]

    def test_admin_endpoints_require_admin_privileges(self, client: TestClient, regular_token: str, db: Session):
        """Test that admin endpoints require admin privileges."""
        # Create test data
        from app.models import Team, League

        league = League(name="Test League", invite_code="TEST123")
        db.add(league)
        db.flush()

        team = Team(name="Test Team", league_id=league.id)
        db.add(team)
        db.commit()

        # Test grant moves
        response = client.post(
            f"/api/v1/admin/teams/{team.id}/weeks/1/grant-moves",
            headers={"Authorization": f"Bearer {regular_token}"},
            json={
                "moves_to_grant": 2,
                "reason": "Test",
                "week_id": 1
            }
        )
        assert response.status_code == 403

        # Test move summary
        response = client.get(
            f"/api/v1/admin/teams/{team.id}/weeks/1/move-summary",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403

        # Test force roster
        response = client.put(
            f"/api/v1/admin/teams/{team.id}/weeks/1/force-roster",
            headers={"Authorization": f"Bearer {regular_token}"},
            json={
                "starter_ids": [1, 2, 3, 4, 5],
                "week_id": 1,
                "bypass_move_limit": True
            }
        )
        assert response.status_code == 403