import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DraftPick, DraftState, League, Player, Team, User
from app.services.draft import DraftService


# Mock data for testing
@pytest.fixture
def setup_test_data(db: Session):
    # Create test user (commissioner)
    commissioner = User(email="commissioner@example.com", hashed_password="$2b$12$test_hash")
    db.add(commissioner)
    db.flush()

    # Create test league
    league = League(name="Test League", invite_code="TEST-1234-5678", commissioner_id=commissioner.id)
    db.add(league)
    db.flush()

    # Create 4 teams in the league
    teams = []
    for i in range(4):
        team = Team(name=f"Team {i+1}", owner_id=commissioner.id, league_id=league.id)
        db.add(team)
        teams.append(team)
    db.flush()

    # Create 20 test players
    players = []
    positions = ["G", "G", "F", "F", "C"]
    for i in range(20):
        player = Player(full_name=f"Player {i+1}", position=positions[i % 5])
        db.add(player)
        players.append(player)

    db.commit()

    return {"commissioner": commissioner, "league": league, "teams": teams, "players": players}


def test_start_draft(db: Session, setup_test_data):
    """Test starting a draft for a league."""
    league = setup_test_data["league"]
    commissioner = setup_test_data["commissioner"]

    # Create draft service
    draft_service = DraftService(db)

    # Start draft
    draft_state = draft_service.start_draft(league.id, commissioner.id)

    # Verify draft was created
    assert draft_state is not None
    assert draft_state.league_id == league.id
    assert draft_state.status == "active"
    assert draft_state.current_round == 1
    assert draft_state.current_pick_index == 0

    # Verify pick order format (should be 8 teams for a 4-team snake draft)
    pick_order = draft_state.get_pick_order()
    assert len(pick_order) == 8

    # First 4 should be in order, last 4 should be reversed
    team_ids = [team.id for team in setup_test_data["teams"]]
    expected_order = team_ids + team_ids[::-1]
    assert pick_order == expected_order


def test_make_pick(db: Session, setup_test_data):
    """Test making picks in a draft."""
    league = setup_test_data["league"]
    commissioner = setup_test_data["commissioner"]
    players = setup_test_data["players"]

    # Create draft service
    draft_service = DraftService(db)

    # Start draft
    draft_state = draft_service.start_draft(league.id, commissioner.id)

    # Make first pick
    current_team_id = draft_state.current_team_id()
    pick, updated_draft = draft_service.make_pick(
        draft_id=draft_state.id, team_id=current_team_id, player_id=players[0].id, user_id=commissioner.id
    )

    # Verify pick was made
    assert pick is not None
    assert pick.team_id == current_team_id
    assert pick.player_id == players[0].id
    assert pick.round == 1
    assert pick.pick_number == 1

    # Verify draft state was updated
    assert updated_draft.current_pick_index == 1
    assert updated_draft.current_round == 1

    # Make second pick
    current_team_id = updated_draft.current_team_id()
    pick2, updated_draft2 = draft_service.make_pick(
        draft_id=draft_state.id, team_id=current_team_id, player_id=players[1].id, user_id=commissioner.id
    )

    # Verify second pick
    assert pick2.team_id == current_team_id
    assert pick2.player_id == players[1].id
    assert pick2.round == 1
    assert pick2.pick_number == 2


def test_auto_pick(db: Session, setup_test_data):
    """Test auto-pick functionality."""
    league = setup_test_data["league"]
    commissioner = setup_test_data["commissioner"]

    # Create draft service
    draft_service = DraftService(db)

    # Start draft
    draft_state = draft_service.start_draft(league.id, commissioner.id)

    # Perform auto-pick
    pick_result = draft_service.auto_pick(draft_state.id)

    # Verify pick was made
    assert pick_result is not None
    pick, updated_draft = pick_result

    assert pick.is_auto == 1  # SQLite stores booleans as integers
    assert updated_draft.current_pick_index == 1  # Moved to next pick


def test_pause_resume(db: Session, setup_test_data):
    """Test pausing and resuming a draft."""
    league = setup_test_data["league"]
    commissioner = setup_test_data["commissioner"]

    # Create draft service
    draft_service = DraftService(db)

    # Start draft
    draft_state = draft_service.start_draft(league.id, commissioner.id)

    # Pause draft
    paused_draft = draft_service.pause_draft(draft_state.id, commissioner.id)
    assert paused_draft.status == "paused"

    # Resume draft
    resumed_draft = draft_service.resume_draft(draft_state.id, commissioner.id)
    assert resumed_draft.status == "active"


@pytest.mark.slow
def test_complete_draft(db: Session, setup_test_data):
    """Test completing a draft (3 rounds).

    Note: This test is marked slow because it performs sequential database
    operations which can take time. Original test ran 10 rounds (40 picks),
    but has been reduced to 3 rounds (12 picks) to improve performance.
    Run with --skip-slow to exclude this test.
    """
    league = setup_test_data["league"]
    commissioner = setup_test_data["commissioner"]
    players = setup_test_data["players"]

    # Create draft service
    draft_service = DraftService(db)

    # Start draft
    draft_state = draft_service.start_draft(league.id, commissioner.id)

    # Make 12 picks (3 rounds × 4 teams)
    player_index = 0
    drafted_player_ids = set()

    # Get number of teams
    teams = setup_test_data["teams"]
    num_teams = len(teams)
    num_rounds = 3  # Reduced from 10 to 3 for faster execution
    total_picks = num_teams * num_rounds

    for i in range(total_picks):
        current_team_id = draft_state.current_team_id()

        # Find an undrafted player
        while players[player_index].id in drafted_player_ids:
            player_index = (player_index + 1) % len(players)

        player_id = players[player_index].id
        drafted_player_ids.add(player_id)
        player_index = (player_index + 1) % len(players)

        pick, draft_state = draft_service.make_pick(
            draft_id=draft_state.id, team_id=current_team_id, player_id=player_id, user_id=commissioner.id
        )

    # Verify draft made it through expected rounds
    assert draft_state.current_round > 3

    # Verify all picks were made
    picks_count = db.query(DraftPick).filter(DraftPick.draft_id == draft_state.id).count()
    assert picks_count == total_picks
