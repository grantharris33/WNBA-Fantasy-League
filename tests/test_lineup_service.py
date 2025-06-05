import pytest
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import Session

from app.models import Team, Player, RosterSlot, WeeklyLineup, League, User
from app.services.lineup import LineupService


@pytest.fixture
def lineup_service(db: Session):
    """Create a LineupService instance."""
    return LineupService(db)


@pytest.fixture
def setup_lineup_test(db: Session):
    """Set up test data for lineup tests."""
    # Create user and league
    user = User(email="test@example.com", hashed_password="hashed")
    league = League(name="Test League", invite_code="TEST123")
    db.add_all([user, league])
    db.flush()

    # Create team
    team = Team(name="Test Team", owner_id=user.id, league_id=league.id)
    db.add(team)
    db.flush()

    # Create players
    players = []
    for i in range(7):
        player = Player(
            full_name=f"Player {i+1}",
            position="G" if i < 2 else ("F" if i < 5 else "C"),
            team_abbr="TEST"
        )
        players.append(player)

    db.add_all(players)
    db.flush()

    # Create roster slots (first 5 as starters)
    roster_slots = []
    for i, player in enumerate(players):
        slot = RosterSlot(
            team_id=team.id,
            player_id=player.id,
            position=player.position,
            is_starter=i < 5  # First 5 are starters
        )
        roster_slots.append(slot)

    db.add_all(roster_slots)
    db.commit()

    return {
        "user": user,
        "league": league,
        "team": team,
        "players": players,
        "roster_slots": roster_slots
    }


def test_week_bounds(lineup_service):
    """Test week bounds calculation."""
    # Test a known Monday
    monday = date(2025, 1, 6)  # This is a Monday
    start, end, week_id = lineup_service._week_bounds(monday)

    assert start.date() == monday
    assert start.time() == datetime.min.time()
    assert end.date() == date(2025, 1, 13)  # Next Monday
    assert week_id == 202502  # 2025 week 2


def test_get_current_week_id(lineup_service):
    """Test getting current week ID."""
    week_id = lineup_service.get_current_week_id()
    assert isinstance(week_id, int)
    assert week_id > 202500  # Should be a valid week ID


def test_can_modify_lineup_current_week(lineup_service, setup_lineup_test):
    """Test lineup modification for current week."""
    team = setup_lineup_test["team"]
    current_week_id = lineup_service.get_current_week_id()

    # Should be able to modify current week if not locked
    assert lineup_service.can_modify_lineup(team.id, current_week_id) is True


def test_can_modify_lineup_past_week(lineup_service, setup_lineup_test):
    """Test lineup modification for past week."""
    team = setup_lineup_test["team"]
    past_week_id = 202501  # Assuming this is in the past

    # Should not be able to modify past week
    assert lineup_service.can_modify_lineup(team.id, past_week_id) is False


def test_can_modify_lineup_locked_week(lineup_service, setup_lineup_test, db):
    """Test lineup modification for locked week."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]
    week_id = 202510  # Future week

    # Lock the lineup
    locked_at = datetime.now(timezone.utc)
    for i, player in enumerate(players[:5]):  # Lock first 5 players
        weekly_lineup = WeeklyLineup(
            team_id=team.id,
            player_id=player.id,
            week_id=week_id,
            is_starter=True,
            locked_at=locked_at
        )
        db.add(weekly_lineup)
    db.commit()

    # Should not be able to modify locked week
    assert lineup_service.can_modify_lineup(team.id, week_id) is False


def test_lock_weekly_lineups(lineup_service, setup_lineup_test, db):
    """Test locking weekly lineups."""
    team = setup_lineup_test["team"]
    week_id = 202510  # Future week

    # Lock lineups
    teams_processed = lineup_service.lock_weekly_lineups(week_id)

    assert teams_processed == 1

    # Verify lineups were created
    lineups = db.query(WeeklyLineup).filter(
        WeeklyLineup.team_id == team.id,
        WeeklyLineup.week_id == week_id
    ).all()

    assert len(lineups) == 7  # All 7 players

    # Check starters
    starters = [lineup for lineup in lineups if lineup.is_starter]
    assert len(starters) == 5


def test_lock_weekly_lineups_already_locked(lineup_service, setup_lineup_test, db):
    """Test locking lineups when already locked."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]
    week_id = 202510

    # Pre-lock one player
    weekly_lineup = WeeklyLineup(
        team_id=team.id,
        player_id=players[0].id,
        week_id=week_id,
        is_starter=True,
        locked_at=datetime.now(timezone.utc)
    )
    db.add(weekly_lineup)
    db.commit()

    # Try to lock again
    teams_processed = lineup_service.lock_weekly_lineups(week_id)

    # Should skip already locked team
    assert teams_processed == 0


def test_set_weekly_starters_current_week(lineup_service, setup_lineup_test, db):
    """Test setting starters for current week."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]
    current_week_id = lineup_service.get_current_week_id()

    # Change starters (use last 5 players instead of first 5)
    new_starter_ids = [p.id for p in players[2:7]]

    success = lineup_service.set_weekly_starters(team.id, current_week_id, new_starter_ids)
    assert success is True

    # Verify changes in RosterSlot table
    roster_slots = db.query(RosterSlot).filter(RosterSlot.team_id == team.id).all()
    starter_slots = [rs for rs in roster_slots if rs.is_starter]

    assert len(starter_slots) == 5
    starter_player_ids = [rs.player_id for rs in starter_slots]
    assert set(starter_player_ids) == set(new_starter_ids)

    # Verify moves counter incremented
    updated_team = db.query(Team).filter(Team.id == team.id).first()
    assert updated_team.moves_this_week == 1


def test_set_weekly_starters_locked_week(lineup_service, setup_lineup_test, db):
    """Test setting starters for locked week."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]
    week_id = 202510

    # Lock the lineup first
    lineup_service.lock_weekly_lineups(week_id)

    # Try to set starters
    new_starter_ids = [p.id for p in players[2:7]]
    success = lineup_service.set_weekly_starters(team.id, week_id, new_starter_ids)

    assert success is False


def test_get_weekly_lineup_current_week(lineup_service, setup_lineup_test):
    """Test getting lineup for current week."""
    team = setup_lineup_test["team"]
    current_week_id = lineup_service.get_current_week_id()

    lineup = lineup_service.get_weekly_lineup(team.id, current_week_id)

    assert lineup is not None
    assert len(lineup) == 7  # All players

    starters = [p for p in lineup if p["is_starter"]]
    assert len(starters) == 5

    # Check data structure
    for player_data in lineup:
        assert "player_id" in player_data
        assert "player_name" in player_data
        assert "position" in player_data
        assert "team_abbr" in player_data
        assert "is_starter" in player_data
        assert "locked" in player_data


def test_get_weekly_lineup_past_week_locked(lineup_service, setup_lineup_test, db):
    """Test getting lineup for past locked week."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]
    week_id = 202501  # Past week

    # Create locked lineup
    locked_at = datetime.now(timezone.utc)
    for i, player in enumerate(players):
        weekly_lineup = WeeklyLineup(
            team_id=team.id,
            player_id=player.id,
            week_id=week_id,
            is_starter=i < 5,
            locked_at=locked_at
        )
        db.add(weekly_lineup)
    db.commit()

    lineup = lineup_service.get_weekly_lineup(team.id, week_id)

    assert lineup is not None
    assert len(lineup) == 7

    # All should be locked
    for player_data in lineup:
        assert player_data["locked"] is True
        # Check that locked_at is close to our timestamp (within 1 second)
        assert abs((player_data["locked_at"] - locked_at.replace(tzinfo=None)).total_seconds()) < 1


def test_get_weekly_lineup_nonexistent(lineup_service, setup_lineup_test):
    """Test getting lineup for nonexistent week."""
    team = setup_lineup_test["team"]
    week_id = 202599  # Far future week

    lineup = lineup_service.get_weekly_lineup(team.id, week_id)

    # Should return current roster for future weeks
    assert lineup is not None
    assert len(lineup) == 7


def test_get_lineup_history(lineup_service, setup_lineup_test, db):
    """Test getting lineup history."""
    team = setup_lineup_test["team"]
    players = setup_lineup_test["players"]

    # Create historical lineups for multiple weeks
    weeks = [202501, 202502, 202503]
    for week_id in weeks:
        locked_at = datetime.now(timezone.utc)
        for i, player in enumerate(players):
            weekly_lineup = WeeklyLineup(
                team_id=team.id,
                player_id=player.id,
                week_id=week_id,
                is_starter=i < 5,
                locked_at=locked_at
            )
            db.add(weekly_lineup)
    db.commit()

    history = lineup_service.get_lineup_history(team.id)

    # Should include current week + historical weeks
    assert len(history) >= 4  # 3 historical + current

    # Check structure
    for week_data in history:
        assert "week_id" in week_data
        assert "lineup" in week_data
        assert "is_current" in week_data
        assert len(week_data["lineup"]) == 7

    # Current week should be marked
    current_weeks = [w for w in history if w["is_current"]]
    assert len(current_weeks) == 1


def test_get_lineup_history_no_history(lineup_service, setup_lineup_test):
    """Test getting lineup history with no historical data."""
    team = setup_lineup_test["team"]

    history = lineup_service.get_lineup_history(team.id)

    # Should still include current week
    assert len(history) == 1
    assert history[0]["is_current"] is True