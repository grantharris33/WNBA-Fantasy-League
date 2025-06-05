from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import (
    WeeklyLineup, RosterSlot, Team, Player, TeamScore,
    TransactionLog, User, StatLine, Game
)
from app.services.scoring import update_weekly_team_scores
from app.services.lineup import LineupService


class AdminService:
    """Service for admin-only operations like historical lineup modifications and score recalculation."""

    def __init__(self, db: Session):
        self.db = db
        self.lineup_service = LineupService(db)

    def modify_historical_lineup(
        self,
        team_id: int,
        week_id: int,
        changes: Dict[str, Any],
        admin_user_id: int,
        justification: str = ""
    ) -> bool:
        """
        Modify a historical lineup for a specific team and week.

        Args:
            team_id: The team ID
            week_id: The week ID
            changes: Dictionary with 'starter_ids' list of player IDs to set as starters
            admin_user_id: ID of the admin user making the change
            justification: Reason for the modification

        Returns:
            True if successful, False otherwise
        """
        # Verify team exists
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        # Get current lineup state for comparison
        existing_lineup = (
            self.db.query(WeeklyLineup)
            .filter(WeeklyLineup.team_id == team_id, WeeklyLineup.week_id == week_id)
            .all()
        )

        if not existing_lineup:
            raise ValueError(f"No lineup found for team {team_id}, week {week_id}")

        # Store before state for audit
        before_state = {
            "starters": [lineup.player_id for lineup in existing_lineup if lineup.is_starter],
            "bench": [lineup.player_id for lineup in existing_lineup if not lineup.is_starter]
        }

        # Apply changes
        new_starter_ids = changes.get('starter_ids', [])
        if len(new_starter_ids) != 5:
            raise ValueError("Must specify exactly 5 starters")

        # Update lineup entries
        for lineup_entry in existing_lineup:
            lineup_entry.is_starter = lineup_entry.player_id in new_starter_ids

        # Store after state for audit
        after_state = {
            "starters": new_starter_ids,
            "bench": [lineup.player_id for lineup in existing_lineup if not lineup.is_starter]
        }

        # Log the admin action
        self._log_admin_action(
            admin_user_id=admin_user_id,
            action="MODIFY_HISTORICAL_LINEUP",
            details=f"Team {team_id}, Week {week_id}: {justification}",
            before_state=before_state,
            after_state=after_state
        )

        self.db.commit()
        return True

    def recalculate_team_week_score(
        self,
        team_id: int,
        week_id: int,
        admin_user_id: int,
        justification: str = ""
    ) -> Optional[float]:
        """
        Recalculate the score for a specific team and week.

        Args:
            team_id: The team ID
            week_id: The week ID
            admin_user_id: ID of the admin user making the change
            justification: Reason for the recalculation

        Returns:
            The new score or None if calculation failed
        """
        # Get existing score for comparison
        existing_score = (
            self.db.query(TeamScore)
            .filter(TeamScore.team_id == team_id, TeamScore.week == week_id)
            .first()
        )

        old_score = existing_score.score if existing_score else 0.0

        # Recalculate using the scoring service
        # Convert week_id to a date in that week for the scoring function
        # Week ID format: year * 100 + iso_week (e.g., 202502 = 2025 week 2)
        year = week_id // 100
        iso_week = week_id % 100

        # Get a Monday date in that week for scoring calculation
        from datetime import date, timedelta
        import datetime as dt

        # Find the first Monday of the year, then add weeks
        jan_4 = date(year, 1, 4)  # Week 1 always contains Jan 4
        jan_4_weekday = jan_4.weekday()
        first_monday = jan_4 - timedelta(days=jan_4_weekday)
        target_date = first_monday + timedelta(weeks=iso_week - 1)

        update_weekly_team_scores(target_date, session=self.db)

        # Get the new score
        new_score_entry = (
            self.db.query(TeamScore)
            .filter(TeamScore.team_id == team_id, TeamScore.week == week_id)
            .first()
        )

        new_score = new_score_entry.score if new_score_entry else 0.0

        # Log the admin action
        self._log_admin_action(
            admin_user_id=admin_user_id,
            action="RECALCULATE_SCORE",
            details=f"Team {team_id}, Week {week_id}: {justification}",
            before_state={"score": old_score},
            after_state={"score": new_score}
        )

        return new_score

    def override_weekly_moves(
        self,
        team_id: int,
        additional_moves: int,
        admin_user_id: int,
        justification: str = ""
    ) -> bool:
        """
        Grant additional weekly moves to a team.

        Args:
            team_id: The team ID
            additional_moves: Number of additional moves to grant
            admin_user_id: ID of the admin user making the change
            justification: Reason for granting moves

        Returns:
            True if successful
        """
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError(f"Team with ID {team_id} not found")

        old_moves = team.moves_this_week
        team.moves_this_week = max(0, team.moves_this_week - additional_moves)
        new_moves = team.moves_this_week

        # Log the admin action
        self._log_admin_action(
            admin_user_id=admin_user_id,
            action="OVERRIDE_WEEKLY_MOVES",
            details=f"Team {team_id}: Granted {additional_moves} moves. {justification}",
            before_state={"moves_this_week": old_moves},
            after_state={"moves_this_week": new_moves}
        )

        self.db.commit()
        return True

    def get_admin_audit_log(
        self,
        team_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get admin action audit log.

        Args:
            team_id: Optional team ID to filter by
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log entries
        """
        query = (
            self.db.query(TransactionLog, User.email)
            .join(User, TransactionLog.user_id == User.id)
            .filter(TransactionLog.action.in_([
                'MODIFY_HISTORICAL_LINEUP',
                'RECALCULATE_SCORE',
                'OVERRIDE_WEEKLY_MOVES'
            ]))
            .order_by(desc(TransactionLog.timestamp))
        )

        if team_id:
            query = query.filter(TransactionLog.patch.contains(f"Team {team_id}"))

        logs = query.offset(offset).limit(limit).all()

        result = []
        for log, admin_email in logs:
            result.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "admin_email": admin_email,
                "action": log.action,
                "details": log.patch,  # We store details in patch field
                "path": log.path,
                "method": log.method
            })

        return result

    def _log_admin_action(
        self,
        admin_user_id: int,
        action: str,
        details: str,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None
    ) -> None:
        """
        Log an admin action to the audit trail.

        Args:
            admin_user_id: ID of the admin user
            action: Type of action performed
            details: Human-readable description
            before_state: State before the change
            after_state: State after the change
        """
        import json

        patch_data = {
            "details": details,
            "before": before_state,
            "after": after_state
        }

        log_entry = TransactionLog(
            user_id=admin_user_id,
            action=action,
            method="ADMIN",
            path="/admin/action",
            patch=json.dumps(patch_data),
            timestamp=datetime.now(timezone.utc)
        )

        self.db.add(log_entry)
        self.db.flush()  # Ensure the log entry is written to DB

    def get_team_lineup_history(self, team_id: int) -> List[Dict[str, Any]]:
        """
        Get the lineup history for a team across all weeks.

        Args:
            team_id: The team ID

        Returns:
            List of weekly lineups with modification history
        """
        # Get all weeks that have lineups for this team
        weeks = (
            self.db.query(WeeklyLineup.week_id)
            .filter(WeeklyLineup.team_id == team_id)
            .distinct()
            .order_by(desc(WeeklyLineup.week_id))
            .all()
        )

        result = []
        for (week_id,) in weeks:
            lineup = self.lineup_service.get_weekly_lineup(team_id, week_id)
            if lineup:
                # Check if this lineup was modified by admin
                admin_logs = (
                    self.db.query(TransactionLog)
                    .filter(
                        TransactionLog.action == 'MODIFY_HISTORICAL_LINEUP',
                        TransactionLog.patch.contains(f"Team {team_id}, Week {week_id}")
                    )
                    .order_by(desc(TransactionLog.timestamp))
                    .all()
                )

                result.append({
                    "week_id": week_id,
                    "lineup": lineup,
                    "admin_modified": len(admin_logs) > 0,
                    "modification_count": len(admin_logs),
                    "last_modified": admin_logs[0].timestamp.isoformat() if admin_logs else None
                })

        return result