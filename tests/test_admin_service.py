"""Tests for admin service functionality."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import User, Team, WeeklyLineup, TeamScore, TransactionLog, Player, RosterSlot
from app.services.admin import AdminService
from app.core.security import hash_password


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
            locked_at=datetime.now(timezone.utc)
        )
        db.add(lineup_entry)
        lineup_entries.append(lineup_entry)

    db.commit()
    return lineup_entries


@pytest.fixture
def test_team_score(db: Session, test_team: Team):
    """Create a test team score."""
    score = TeamScore(
        team_id=test_team.id,
        week=202501,
        score=85.5
    )
    db.add(score)
    db.commit()
    return score


class TestAdminService:
    """Test cases for AdminService."""

    def test_modify_historical_lineup_success(self, db: Session, admin_user: User, test_team: Team, test_weekly_lineup: list, test_players: list):
        """Test successful historical lineup modification."""
        admin_service = AdminService(db)

        # Get new starter IDs (different from current)
        new_starter_ids = [p.id for p in test_players[2:7]]  # Different 5 players

        result = admin_service.modify_historical_lineup(
            team_id=test_team.id,
            week_id=202501,
            changes={"starter_ids": new_starter_ids},
            admin_user_id=admin_user.id,
            justification="Testing lineup modification"
        )

        assert result is True

        # Verify lineup was updated
        updated_lineup = db.query(WeeklyLineup).filter(
            WeeklyLineup.team_id == test_team.id,
            WeeklyLineup.week_id == 202501
        ).all()

        starters = [entry for entry in updated_lineup if entry.is_starter]
        starter_ids = [entry.player_id for entry in starters]

        assert len(starters) == 5
        assert set(starter_ids) == set(new_starter_ids)

        # Verify audit log was created
        audit_log = db.query(TransactionLog).filter(
            TransactionLog.action == "MODIFY_HISTORICAL_LINEUP"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == admin_user.id

    def test_modify_historical_lineup_invalid_team(self, db: Session, admin_user: User):
        """Test lineup modification with invalid team ID."""
        admin_service = AdminService(db)

        with pytest.raises(ValueError, match="Team with ID 999 not found"):
            admin_service.modify_historical_lineup(
                team_id=999,
                week_id=202501,
                changes={"starter_ids": [1, 2, 3, 4, 5]},
                admin_user_id=admin_user.id,
                justification="Test"
            )

    def test_modify_historical_lineup_no_lineup(self, db: Session, admin_user: User, test_team: Team):
        """Test lineup modification when no lineup exists."""
        admin_service = AdminService(db)

        with pytest.raises(ValueError, match="No lineup found"):
            admin_service.modify_historical_lineup(
                team_id=test_team.id,
                week_id=202502,  # Different week with no lineup
                changes={"starter_ids": [1, 2, 3, 4, 5]},
                admin_user_id=admin_user.id,
                justification="Test"
            )

    def test_modify_historical_lineup_wrong_starter_count(self, db: Session, admin_user: User, test_team: Team, test_weekly_lineup: list):
        """Test lineup modification with wrong number of starters."""
        admin_service = AdminService(db)

        with pytest.raises(ValueError, match="Must specify exactly 5 starters"):
            admin_service.modify_historical_lineup(
                team_id=test_team.id,
                week_id=202501,
                changes={"starter_ids": [1, 2, 3]},  # Only 3 starters
                admin_user_id=admin_user.id,
                justification="Test"
            )

    def test_recalculate_team_week_score(self, db: Session, admin_user: User, test_team: Team, test_team_score: TeamScore):
        """Test score recalculation."""
        admin_service = AdminService(db)

        old_score = test_team_score.score

        # Mock the scoring calculation by directly updating the score
        # In a real scenario, this would trigger the actual scoring calculation
        new_score = admin_service.recalculate_team_week_score(
            team_id=test_team.id,
            week_id=202501,
            admin_user_id=admin_user.id,
            justification="Testing score recalculation"
        )

        # Verify audit log was created
        audit_log = db.query(TransactionLog).filter(
            TransactionLog.action == "RECALCULATE_SCORE"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == admin_user.id

    def test_override_weekly_moves(self, db: Session, admin_user: User, test_team: Team):
        """Test granting additional weekly moves."""
        admin_service = AdminService(db)

        original_moves = test_team.moves_this_week
        additional_moves = 2

        result = admin_service.override_weekly_moves(
            team_id=test_team.id,
            additional_moves=additional_moves,
            admin_user_id=admin_user.id,
            justification="Testing move override"
        )

        assert result is True

        # Verify moves were updated
        db.refresh(test_team)
        expected_moves = max(0, original_moves - additional_moves)
        assert test_team.moves_this_week == expected_moves

        # Verify audit log was created
        audit_log = db.query(TransactionLog).filter(
            TransactionLog.action == "OVERRIDE_WEEKLY_MOVES"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == admin_user.id

    def test_override_weekly_moves_invalid_team(self, db: Session, admin_user: User):
        """Test move override with invalid team ID."""
        admin_service = AdminService(db)

        with pytest.raises(ValueError, match="Team with ID 999 not found"):
            admin_service.override_weekly_moves(
                team_id=999,
                additional_moves=2,
                admin_user_id=admin_user.id,
                justification="Test"
            )

    def test_get_admin_audit_log(self, db: Session, admin_user: User, test_team: Team, test_weekly_lineup: list, test_players: list):
        """Test retrieving admin audit log."""
        admin_service = AdminService(db)

        # Perform some admin actions to create audit entries
        admin_service.modify_historical_lineup(
            team_id=test_team.id,
            week_id=202501,
            changes={"starter_ids": [p.id for p in test_players[2:7]]},
            admin_user_id=admin_user.id,
            justification="Test action 1"
        )

        admin_service.override_weekly_moves(
            team_id=test_team.id,
            additional_moves=1,
            admin_user_id=admin_user.id,
            justification="Test action 2"
        )

        # Get audit log
        logs = admin_service.get_admin_audit_log()

        assert len(logs) >= 2

        # Check log structure
        for log in logs:
            assert "id" in log
            assert "timestamp" in log
            assert "admin_email" in log
            assert "action" in log
            assert "details" in log

    def test_get_admin_audit_log_filtered_by_team(self, db: Session, admin_user: User, test_team: Team, test_weekly_lineup: list, test_players: list):
        """Test retrieving audit log filtered by team."""
        admin_service = AdminService(db)

        # Perform admin action
        admin_service.modify_historical_lineup(
            team_id=test_team.id,
            week_id=202501,
            changes={"starter_ids": [p.id for p in test_players[2:7]]},
            admin_user_id=admin_user.id,
            justification="Test action"
        )

        # Get audit log filtered by team
        logs = admin_service.get_admin_audit_log(team_id=test_team.id)

        assert len(logs) >= 1

        # All logs should be related to the team
        for log in logs:
            assert f"Team {test_team.id}" in log["details"]

    def test_get_team_lineup_history(self, db: Session, admin_user: User, test_team: Team, test_weekly_lineup: list, test_players: list):
        """Test retrieving team lineup history."""
        admin_service = AdminService(db)

        # Modify lineup to create history
        admin_service.modify_historical_lineup(
            team_id=test_team.id,
            week_id=202501,
            changes={"starter_ids": [p.id for p in test_players[2:7]]},
            admin_user_id=admin_user.id,
            justification="Test modification"
        )

        # Get lineup history
        history = admin_service.get_team_lineup_history(test_team.id)

        assert len(history) >= 1

        # Check history structure
        for entry in history:
            assert "week_id" in entry
            assert "lineup" in entry
            assert "admin_modified" in entry
            assert "modification_count" in entry

        # At least one entry should show admin modification
        modified_entries = [entry for entry in history if entry["admin_modified"]]
        assert len(modified_entries) >= 1

    def test_log_admin_action(self, db: Session, admin_user: User):
        """Test internal admin action logging."""
        admin_service = AdminService(db)

        before_state = {"test": "before"}
        after_state = {"test": "after"}

        admin_service._log_admin_action(
            admin_user_id=admin_user.id,
            action="TEST_ACTION",
            details="Test details",
            before_state=before_state,
            after_state=after_state
        )

        db.commit()

        # Verify log was created
        log = db.query(TransactionLog).filter(
            TransactionLog.action == "TEST_ACTION"
        ).first()

        assert log is not None
        assert log.user_id == admin_user.id
        assert log.method == "ADMIN"
        assert log.path == "/admin/action"

        # Verify patch data contains before/after states
        import json
        patch_data = json.loads(log.patch)
        assert patch_data["before"] == before_state
        assert patch_data["after"] == after_state