import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.jobs.draft_clock import check_draft_clocks, pause_stale_drafts
from app.models import DraftState, League, User, Team, Player
from app.services.draft import DraftService


@pytest.fixture
def setup_active_draft(db: Session):
    """Set up an active draft for testing."""
    # Create test user
    user = User(
        email="commissioner@example.com",
        hashed_password="$2b$12$test_hash"
    )
    db.add(user)
    db.flush()

    # Create test league
    league = League(
        name="Test League",
        commissioner_id=user.id
    )
    db.add(league)
    db.flush()

    # Create 4 teams
    teams = []
    for i in range(4):
        team = Team(
            name=f"Team {i+1}",
            owner_id=user.id,
            league_id=league.id
        )
        db.add(team)
        teams.append(team)
    db.flush()

    # Create 10 test players
    players = []
    for i in range(10):
        player = Player(
            full_name=f"Player {i+1}",
            position="G" if i % 2 == 0 else "F"
        )
        db.add(player)
        players.append(player)

    # Create active draft
    team_ids = [team.id for team in teams]
    pick_order = ",".join(map(str, team_ids + team_ids[::-1]))

    draft_state = DraftState(
        league_id=league.id,
        status="active",
        pick_order=pick_order,
        current_round=1,
        current_pick_index=0,
        seconds_remaining=10,  # Set to 10 seconds for testing
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(draft_state)
    db.commit()

    return {
        "user": user,
        "league": league,
        "teams": teams,
        "players": players,
        "draft": draft_state
    }


@patch("app.jobs.draft_clock.DraftService")
def test_check_draft_clocks_auto_pick(mock_draft_service, db: Session, setup_active_draft):
    """Test that check_draft_clocks triggers auto-pick when the timer expires."""
    # Get the active draft
    draft = setup_active_draft["draft"]

    # Set up mock
    mock_service_instance = MagicMock()
    mock_draft_service.return_value = mock_service_instance

    # Set up a mock auto_pick result
    mock_pick = MagicMock()
    mock_updated_draft = MagicMock()
    mock_service_instance.auto_pick.return_value = (mock_pick, mock_updated_draft)

    # Check the draft clock with timer at 1 second (will be decremented to 0)
    draft.seconds_remaining = 1
    db.add(draft)
    db.commit()

    # Run the check_draft_clocks function
    check_draft_clocks()

    # Verify auto_pick was called
    mock_service_instance.auto_pick.assert_called_once_with(draft.id)

    # Refresh the draft state
    db.refresh(draft)

    # Timer should have been decremented
    assert draft.seconds_remaining == 0


@freeze_time("2023-07-01 12:00:00")
def test_stale_draft_detection(db: Session, setup_active_draft):
    """Test that stale drafts are detected and paused."""
    draft = setup_active_draft["draft"]

    # Set the draft's updated_at to 2 hours ago
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    draft.updated_at = two_hours_ago
    db.add(draft)
    db.commit()

    # Run the pause_stale_drafts function
    pause_stale_drafts()

    # Refresh the draft state
    db.refresh(draft)

    # Verify the draft is now paused
    assert draft.status == "paused"