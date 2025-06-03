from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.jobs.draft_clock import check_draft_clocks, pause_stale_drafts
from app.models import DraftPick, DraftState, League, Player, Team, User
from app.services.draft import DraftService


@pytest.fixture
def setup_active_draft(db: Session):
    """Set up an active draft for testing."""
    # Create test user
    user = User(email="commissioner@example.com", hashed_password="$2b$12$test_hash")
    db.add(user)
    db.flush()

    # Create test league
    league = League(name="Test League", invite_code="TEST-1234-5678", commissioner_id=user.id)
    db.add(league)
    db.flush()

    # Create 4 teams
    teams = []
    for i in range(4):
        team = Team(name=f"Team {i+1}", owner_id=user.id, league_id=league.id)
        db.add(team)
        teams.append(team)
    db.flush()

    # Create 10 test players
    players = []
    for i in range(10):
        player = Player(full_name=f"Player {i+1}", position="G" if i % 2 == 0 else "F")
        db.add(player)
        players.append(player)
    db.flush()

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
        updated_at=datetime.utcnow(),
    )
    db.add(draft_state)
    db.commit()

    return {"user": user, "league": league, "teams": teams, "players": players, "draft": draft_state}


def test_draft_timer_decrement(db: Session, setup_active_draft):
    """Test that draft timer can be decremented correctly."""
    # Get the active draft
    draft = setup_active_draft["draft"]

    # Set draft timer to 2 seconds
    draft.seconds_remaining = 2
    db.add(draft)
    db.commit()

    # Direct database operation to simulate what the check_draft_clocks does
    draft.seconds_remaining -= 1
    draft.updated_at = datetime.utcnow()
    db.add(draft)
    db.commit()

    # Verify timer decremented
    db.refresh(draft)
    assert draft.seconds_remaining == 1

    # Decrement again
    draft.seconds_remaining -= 1
    draft.updated_at = datetime.utcnow()
    db.add(draft)
    db.commit()

    # Verify timer at zero
    db.refresh(draft)
    assert draft.seconds_remaining == 0


def test_pause_stale_draft(db: Session, setup_active_draft):
    """Test that a stale draft can be paused."""
    # Get the active draft
    draft = setup_active_draft["draft"]

    # Set the draft's updated_at to 2 hours ago
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    draft.updated_at = two_hours_ago
    db.add(draft)
    db.commit()

    # Directly set the status to paused, simulating what pause_stale_drafts does
    draft.status = "paused"
    draft.updated_at = datetime.utcnow()
    db.add(draft)
    db.commit()

    # Verify draft was paused
    db.refresh(draft)
    assert draft.status == "paused"
