from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models import League, Team, TransactionLog, User
from app.services.team import TeamService
from app.api.schemas import TeamUpdate


@pytest.fixture
def setup_team_test(db: Session):
    """Create test data for team service tests."""
    # Create test users
    user1 = User(email="user1@example.com", hashed_password="hashed_password")
    user2 = User(email="user2@example.com", hashed_password="hashed_password")
    db.add_all([user1, user2])
    db.flush()

    # Create test leagues
    league1 = League(name="Test League 1")
    league2 = League(name="Test League 2")
    db.add_all([league1, league2])
    db.flush()

    # Create test teams
    team1 = Team(name="Team 1", owner_id=user1.id, league_id=league1.id)
    team2 = Team(name="Team 2", owner_id=user2.id, league_id=league1.id)
    team3 = Team(name="Team 3", owner_id=user1.id, league_id=league2.id)
    db.add_all([team1, team2, team3])
    db.commit()

    return {
        "users": [user1, user2],
        "leagues": [league1, league2],
        "teams": [team1, team2, team3],
    }


def test_get_team_by_id(db: Session, setup_team_test):
    """Test retrieving a team by ID."""
    team_id = setup_team_test["teams"][0].id
    team = TeamService.get_team_by_id(db, team_id)

    assert team is not None
    assert team.id == team_id
    assert team.name == "Team 1"

    # Test non-existent team
    non_existent_team = TeamService.get_team_by_id(db, 9999)
    assert non_existent_team is None


def test_get_teams_by_owner_id(db: Session, setup_team_test):
    """Test retrieving teams by owner ID."""
    owner_id = setup_team_test["users"][0].id
    teams = TeamService.get_teams_by_owner_id(db, owner_id)

    assert len(teams) == 2  # User1 has teams in both leagues
    assert any(t.name == "Team 1" for t in teams)
    assert any(t.name == "Team 3" for t in teams)

    # Test owner with no teams
    non_existent_owner_id = 9999
    teams = TeamService.get_teams_by_owner_id(db, non_existent_owner_id)
    assert len(teams) == 0


def test_get_teams_by_league_id(db: Session, setup_team_test):
    """Test retrieving teams by league ID."""
    league_id = setup_team_test["leagues"][0].id
    teams = TeamService.get_teams_by_league_id(db, league_id)

    assert len(teams) == 2  # League1 has 2 teams
    assert any(t.name == "Team 1" for t in teams)
    assert any(t.name == "Team 2" for t in teams)

    # Test league with no teams
    non_existent_league_id = 9999
    teams = TeamService.get_teams_by_league_id(db, non_existent_league_id)
    assert len(teams) == 0


def test_create_team_in_league_success(db: Session, setup_team_test):
    """Test successfully creating a team in a league."""
    league_id = setup_team_test["leagues"][0].id
    owner_id = setup_team_test["users"][1].id
    name = "New Team"

    # User2 doesn't have a team in league2 yet
    team = TeamService.create_team_in_league(db, name=name, league_id=setup_team_test["leagues"][1].id, owner_id=owner_id)

    assert team is not None
    assert team.name == name
    assert team.league_id == setup_team_test["leagues"][1].id
    assert team.owner_id == owner_id

    # Verify transaction log was created
    log = db.query(TransactionLog).order_by(TransactionLog.id.desc()).first()
    assert log is not None
    assert log.user_id == owner_id
    assert "CREATE TEAM" in log.action


def test_create_team_league_not_found(db: Session, setup_team_test):
    """Test creating a team with non-existent league."""
    with pytest.raises(ValueError, match="League not found"):
        TeamService.create_team_in_league(
            db,
            name="New Team",
            league_id=9999,  # Non-existent league
            owner_id=setup_team_test["users"][0].id
        )


def test_create_team_duplicate_in_league(db: Session, setup_team_test):
    """Test creating a team with name that already exists in league (case-insensitive)."""
    league_id = setup_team_test["leagues"][0].id
    existing_name = setup_team_test["teams"][0].name

    # Create a new user who doesn't have a team in this league yet
    new_user = User(email="newuser@example.com", hashed_password="hashed_password")
    db.add(new_user)
    db.flush()

    with pytest.raises(ValueError, match="Team name already exists in this league"):
        TeamService.create_team_in_league(
            db,
            name=existing_name,  # Existing name
            league_id=league_id,
            owner_id=new_user.id
        )

    # Test case-insensitive
    with pytest.raises(ValueError, match="Team name already exists in this league"):
        TeamService.create_team_in_league(
            db,
            name=existing_name.upper(),  # Different case
            league_id=league_id,
            owner_id=new_user.id
        )


def test_create_team_one_per_user_per_league(db: Session, setup_team_test):
    """Test that a user can only own one team per league."""
    league_id = setup_team_test["leagues"][0].id
    owner_id = setup_team_test["users"][0].id  # Already has team in league1

    with pytest.raises(ValueError, match="User already owns a team in this league"):
        TeamService.create_team_in_league(
            db,
            name="Another Team",
            league_id=league_id,
            owner_id=owner_id
        )


def test_update_team_details_success(db: Session, setup_team_test):
    """Test successfully updating team details."""
    team_id = setup_team_test["teams"][0].id
    owner_id = setup_team_test["users"][0].id
    new_name = "Updated Team Name"

    updated_team = TeamService.update_team_details(
        db,
        team_id=team_id,
        owner_id=owner_id,
        data=TeamUpdate(name=new_name)
    )

    assert updated_team is not None
    assert updated_team.name == new_name

    # Verify transaction log was created
    log = db.query(TransactionLog).order_by(TransactionLog.id.desc()).first()
    assert log is not None
    assert log.user_id == owner_id
    assert "UPDATE TEAM" in log.action


def test_update_team_not_found(db: Session, setup_team_test):
    """Test updating a non-existent team."""
    result = TeamService.update_team_details(
        db,
        team_id=9999,  # Non-existent team
        owner_id=setup_team_test["users"][0].id,
        data=TeamUpdate(name="New Name")
    )

    assert result is None


def test_update_team_not_owner(db: Session, setup_team_test):
    """Test that only the owner can update team details."""
    team_id = setup_team_test["teams"][0].id  # Owned by user1
    non_owner_id = setup_team_test["users"][1].id  # user2

    with pytest.raises(PermissionError, match="Not team owner"):
        TeamService.update_team_details(
            db,
            team_id=team_id,
            owner_id=non_owner_id,
            data=TeamUpdate(name="New Name")
        )


def test_update_team_duplicate_name(db: Session, setup_team_test):
    """Test updating a team with a name that already exists in the league."""
    team_id = setup_team_test["teams"][0].id
    owner_id = setup_team_test["users"][0].id
    existing_name = setup_team_test["teams"][1].name  # Name of another team in same league

    with pytest.raises(ValueError, match="Team name already exists in this league"):
        TeamService.update_team_details(
            db,
            team_id=team_id,
            owner_id=owner_id,
            data=TeamUpdate(name=existing_name)
        )


def test_update_team_same_name(db: Session, setup_team_test):
    """Test updating a team with its own current name (should be allowed)."""
    team = setup_team_test["teams"][0]
    current_name = team.name

    updated_team = TeamService.update_team_details(
        db,
        team_id=team.id,
        owner_id=team.owner_id,
        data=TeamUpdate(name=current_name)
    )

    # No change, so no update should happen
    assert updated_team is not None
    assert updated_team.name == current_name

    # No transaction log should be created as no actual update occurred
    log = db.query(TransactionLog).order_by(TransactionLog.id.desc()).first()
    assert log is None or "UPDATE TEAM" not in log.action