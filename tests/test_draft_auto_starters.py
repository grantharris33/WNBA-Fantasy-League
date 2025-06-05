import pytest
from sqlalchemy.orm import Session

from app.models import DraftPick, DraftState, League, Player, RosterSlot, Team, User
from app.services.draft import DraftService


@pytest.fixture
def setup_draft_test(db: Session):
    """Setup a complete draft scenario for testing auto-starter functionality."""
    # Create a test league
    league = League(name="Test League", invite_code="DRAFT123")
    db.add(league)
    db.flush()

    # Create test users
    users = [User(email=f"user{i}@example.com", hashed_password="hashed_password") for i in range(1, 5)]  # 4 users
    db.add_all(users)
    db.flush()

    # Create test teams
    teams = [Team(name=f"Team {i}", owner_id=users[i - 1].id, league_id=league.id) for i in range(1, 5)]  # 4 teams
    db.add_all(teams)
    db.flush()

    # Create test players with various positions - enough to satisfy position requirements
    # Need at least 8 guards (2 per team) and 4 forwards/centers (1 per team)
    players = [
        # Guards (16 total)
        *[Player(full_name=f"Guard {i}", position="G", team_abbr="TST") for i in range(1, 17)],
        # Forwards (12 total)
        *[Player(full_name=f"Forward {i}", position="F", team_abbr="TST") for i in range(1, 13)],
        # Centers (8 total)
        *[Player(full_name=f"Center {i}", position="C", team_abbr="TST") for i in range(1, 9)],
        # Multi-position players
        Player(full_name="Guard-Forward 1", position="G-F", team_abbr="TST"),
        Player(full_name="Forward-Center 1", position="F-C", team_abbr="TST"),
        # Fill remaining slots for full draft
        *[Player(full_name=f"Utility {i}", position="F", team_abbr="TST") for i in range(1, 4)],
    ]
    db.add_all(players)
    db.flush()

    # Create draft state
    pick_order = ",".join([str(team.id) for team in teams] + [str(team.id) for team in reversed(teams)])
    draft = DraftState(
        league_id=league.id, current_round=1, current_pick_index=0, status="active", pick_order=pick_order
    )
    db.add(draft)
    db.flush()

    return {"league": league, "users": users, "teams": teams, "players": players, "draft": draft}


def test_auto_set_starters_after_draft_completion(db: Session, setup_draft_test):
    """Test that starters are automatically set when a draft completes."""
    # Arrange
    service = DraftService(db)
    test_data = setup_draft_test
    teams = test_data["teams"]
    players = test_data["players"]
    draft = test_data["draft"]

    # Simulate a complete draft by manually creating picks and roster slots
    pick_number = 1

    # Draft 10 rounds (10 players per team)
    for round_num in range(1, 11):
        for team_index in range(len(teams)):
            # Snake draft: odd rounds go forward, even rounds go backward
            if round_num % 2 == 1:
                team = teams[team_index]
            else:
                team = teams[len(teams) - 1 - team_index]

            # Pick a player
            player = players[pick_number - 1]

            # Create draft pick
            pick = DraftPick(
                draft_id=draft.id,
                team_id=team.id,
                player_id=player.id,
                round=round_num,
                pick_number=pick_number,
                is_auto=False,
            )

            # Create roster slot
            roster_slot = RosterSlot(
                team_id=team.id,
                player_id=player.id,
                position=player.position,
                is_starter=False,  # Initially no starters
            )

            db.add(pick)
            db.add(roster_slot)
            pick_number += 1

    # Set draft as completed
    draft.status = "completed"
    draft.current_round = 11  # Beyond 10 rounds
    db.commit()

    # Act - call the auto-starter function
    service._set_initial_starters_for_all_teams(test_data["league"].id)

    # Assert - check that each team has exactly 5 starters
    for team in teams:
        starters = db.query(RosterSlot).filter(RosterSlot.team_id == team.id, RosterSlot.is_starter == True).all()

        assert len(starters) == 5, f"Team {team.name} should have exactly 5 starters"

        # Verify position requirements
        starter_positions = [db.query(Player).filter(Player.id == slot.player_id).first().position for slot in starters]

        guard_count = sum(1 for pos in starter_positions if pos and 'G' in pos)
        forward_center_count = sum(1 for pos in starter_positions if pos and ('F' in pos or 'C' in pos))

        assert guard_count >= 2, f"Team {team.name} should have at least 2 guards in starting lineup"
        assert forward_center_count >= 1, f"Team {team.name} should have at least 1 forward/center in starting lineup"


def test_auto_starters_prioritize_early_picks(db: Session, setup_draft_test):
    """Test that auto-starter selection prioritizes early draft picks."""
    # Arrange
    service = DraftService(db)
    test_data = setup_draft_test
    team = test_data["teams"][0]  # Test with first team
    players = test_data["players"]
    draft = test_data["draft"]

    # Create a roster with good positional distribution in early picks
    draft_picks_and_slots = [
        (1, players[0]),  # Guard 1 - 1st pick
        (5, players[1]),  # Guard 2 - 5th pick
        (9, players[16]),  # Forward 1 - 9th pick
        (13, players[28]),  # Center 1 - 13th pick
        (17, players[17]),  # Forward 2 - 17th pick
        (21, players[2]),  # Guard 3 - 21st pick (should be bench)
        (25, players[18]),  # Forward 3 - 25th pick (should be bench)
    ]

    for pick_num, player in draft_picks_and_slots:
        pick = DraftPick(
            draft_id=draft.id,
            team_id=team.id,
            player_id=player.id,
            round=(pick_num - 1) // 4 + 1,
            pick_number=pick_num,
            is_auto=False,
        )

        roster_slot = RosterSlot(team_id=team.id, player_id=player.id, position=player.position, is_starter=False)

        db.add(pick)
        db.add(roster_slot)

    db.commit()

    # Act
    service._set_initial_starters_for_team(team.id)

    # Assert
    starters = db.query(RosterSlot).filter(RosterSlot.team_id == team.id, RosterSlot.is_starter == True).all()

    starter_player_ids = [slot.player_id for slot in starters]

    # The first 5 picks should be starters (they meet position requirements)
    expected_starters = [players[0].id, players[1].id, players[16].id, players[28].id, players[17].id]

    assert len(starter_player_ids) == 5
    assert set(starter_player_ids) == set(expected_starters), "Early picks should be selected as starters"


def test_auto_starters_with_insufficient_players(db: Session, setup_draft_test):
    """Test that auto-starter function handles teams with fewer than 5 players."""
    # Arrange
    service = DraftService(db)
    test_data = setup_draft_test
    team = test_data["teams"][0]
    players = test_data["players"]
    draft = test_data["draft"]

    # Create a roster with only 3 players
    for i, player in enumerate(players[:3]):
        pick = DraftPick(
            draft_id=draft.id, team_id=team.id, player_id=player.id, round=1, pick_number=i + 1, is_auto=False
        )

        roster_slot = RosterSlot(team_id=team.id, player_id=player.id, position=player.position, is_starter=False)

        db.add(pick)
        db.add(roster_slot)

    db.commit()

    # Act
    service._set_initial_starters_for_team(team.id)

    # Assert - no starters should be set since there are fewer than 5 players
    starters = db.query(RosterSlot).filter(RosterSlot.team_id == team.id, RosterSlot.is_starter == True).count()

    assert starters == 0, "Teams with fewer than 5 players should not have starters auto-set"


def test_validate_starter_positions(db: Session, setup_draft_test):
    """Test the position validation logic for starter combinations."""
    # Arrange
    service = DraftService(db)
    test_data = setup_draft_test
    players = test_data["players"]

    # Test valid combination (2 Guards, 3 Forwards/Centers)
    valid_combo = (players[0].id, players[1].id, players[16].id, players[17].id, players[28].id)
    player_positions = {
        players[0].id: "G",
        players[1].id: "G",
        players[16].id: "F",
        players[17].id: "F",
        players[28].id: "C",
    }

    assert service._validate_starter_positions(valid_combo, player_positions) is True

    # Test invalid combination (only 1 Guard)
    invalid_combo = (players[0].id, players[16].id, players[17].id, players[18].id, players[28].id)
    invalid_positions = {
        players[0].id: "G",
        players[16].id: "F",
        players[17].id: "F",
        players[18].id: "F",
        players[28].id: "C",
    }

    assert service._validate_starter_positions(invalid_combo, invalid_positions) is False

    # Test valid combination with multi-position players
    multi_combo = (players[0].id, players[36].id, players[37].id, players[16].id, players[28].id)
    multi_positions = {
        players[0].id: "G",
        players[36].id: "G-F",  # Counts as both Guard and Forward
        players[37].id: "F-C",  # Counts as both Forward and Center
        players[16].id: "F",
        players[28].id: "C",
    }

    assert service._validate_starter_positions(multi_combo, multi_positions) is True


def test_draft_completion_triggers_auto_starters(db: Session, setup_draft_test):
    """Test that making the final pick of a draft automatically sets starters."""
    # Arrange
    service = DraftService(db)
    test_data = setup_draft_test
    teams = test_data["teams"]
    players = test_data["players"]
    draft = test_data["draft"]

    # Simulate draft up to the final pick
    pick_number = 1

    # Draft 39 picks (leaving 1 pick to complete the draft)
    for round_num in range(1, 10):  # 9 full rounds
        for team_index in range(len(teams)):
            if round_num % 2 == 1:
                team = teams[team_index]
            else:
                team = teams[len(teams) - 1 - team_index]

            player = players[pick_number - 1]

            pick = DraftPick(
                draft_id=draft.id,
                team_id=team.id,
                player_id=player.id,
                round=round_num,
                pick_number=pick_number,
                is_auto=False,
            )

            roster_slot = RosterSlot(team_id=team.id, player_id=player.id, position=player.position, is_starter=False)

            db.add(pick)
            db.add(roster_slot)
            pick_number += 1

    # Add 3 more picks in round 10
    for team_index in range(3):
        team = teams[len(teams) - 1 - team_index]  # Round 10 goes backward
        player = players[pick_number - 1]

        pick = DraftPick(
            draft_id=draft.id, team_id=team.id, player_id=player.id, round=10, pick_number=pick_number, is_auto=False
        )

        roster_slot = RosterSlot(team_id=team.id, player_id=player.id, position=player.position, is_starter=False)

        db.add(pick)
        db.add(roster_slot)
        pick_number += 1

    # Set draft state to round 10, last pick
    draft.current_round = 10
    draft.current_pick_index = 3
    db.commit()

    # Act - make the final pick
    final_team = teams[0]  # Team that gets the last pick
    final_player = players[pick_number - 1]

    pick, updated_draft = service.make_pick(
        draft_id=draft.id, team_id=final_team.id, player_id=final_player.id, user_id=test_data["users"][0].id
    )

    # Assert - draft should be completed and starters should be set
    assert updated_draft.status == "completed"

    # Check that all teams have starters set
    for team in teams:
        starters = db.query(RosterSlot).filter(RosterSlot.team_id == team.id, RosterSlot.is_starter == True).count()

        assert starters == 5, f"Team {team.name} should have 5 starters after draft completion"
