from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, and_

from app.models import (
    DataQualityCheck, DataValidationRule, DataAnomalyLog,
    Player, Game, StatLine, WNBATeam, Standings
)


class DataQualityService:
    """Service for data quality monitoring, validation, and anomaly detection."""

    def __init__(self, db: Session):
        self.db = db

    # Quality Check Management
    def create_quality_check(
        self,
        check_name: str,
        check_type: str,
        target_table: str,
        check_query: str,
        expected_result: Optional[str] = None,
        failure_threshold: int = 1
    ) -> DataQualityCheck:
        """Create a new data quality check."""
        check = DataQualityCheck(
            check_name=check_name,
            check_type=check_type,
            target_table=target_table,
            check_query=check_query,
            expected_result=expected_result,
            failure_threshold=failure_threshold
        )
        self.db.add(check)
        self.db.commit()
        return check

    def run_quality_check(self, check_id: int) -> bool:
        """Run a specific quality check and update its status."""
        check = self.db.query(DataQualityCheck).filter(DataQualityCheck.id == check_id).first()
        if not check or not check.is_active:
            return False

        try:
            # Execute the check query
            result = self.db.execute(text(check.check_query))
            actual_result = str(result.scalar()) if result.returns_rows else "executed"
            
            # Determine if check passed
            check_passed = True
            if check.expected_result is not None:
                check_passed = actual_result == check.expected_result

            # Update check status
            check.last_run = datetime.now(timezone.utc)
            check.last_result = actual_result
            
            if check_passed:
                check.status = "passed"
                check.consecutive_failures = 0
            else:
                check.status = "failed"
                check.consecutive_failures += 1
                
                # Log anomaly if failure threshold exceeded
                if check.consecutive_failures >= check.failure_threshold:
                    self._log_anomaly(
                        entity_type="data_quality_check",
                        entity_id=str(check.id),
                        anomaly_type="quality_check_failure",
                        description=f"Quality check '{check.check_name}' failed {check.consecutive_failures} consecutive times. Expected: {check.expected_result}, Got: {actual_result}",
                        severity="high" if check.consecutive_failures > 3 else "medium"
                    )

            self.db.commit()
            return check_passed

        except Exception as e:
            check.last_run = datetime.now(timezone.utc)
            check.last_result = f"ERROR: {str(e)}"
            check.status = "failed"
            check.consecutive_failures += 1
            self.db.commit()
            
            self._log_anomaly(
                entity_type="data_quality_check",
                entity_id=str(check.id),
                anomaly_type="check_execution_error",
                description=f"Quality check '{check.check_name}' execution failed: {str(e)}",
                severity="critical"
            )
            return False

    def run_all_active_checks(self) -> Dict[str, Any]:
        """Run all active quality checks."""
        checks = self.db.query(DataQualityCheck).filter(DataQualityCheck.is_active == True).all()
        results = {
            "total_checks": len(checks),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "check_results": []
        }

        for check in checks:
            try:
                passed = self.run_quality_check(check.id)
                results["check_results"].append({
                    "id": check.id,
                    "name": check.check_name,
                    "status": "passed" if passed else "failed",
                    "last_result": check.last_result
                })
                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["errors"] += 1
                results["check_results"].append({
                    "id": check.id,
                    "name": check.check_name,
                    "status": "error",
                    "error": str(e)
                })

        return results

    # Validation Rules Management
    def create_validation_rule(
        self,
        entity_type: str,
        field_name: str,
        rule_type: str,
        rule_config: Dict[str, Any]
    ) -> DataValidationRule:
        """Create a new data validation rule."""
        rule = DataValidationRule(
            entity_type=entity_type,
            field_name=field_name,
            rule_type=rule_type,
            rule_config=rule_config
        )
        self.db.add(rule)
        self.db.commit()
        return rule

    def validate_entity(self, entity_type: str, entity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate an entity against all applicable rules."""
        rules = (
            self.db.query(DataValidationRule)
            .filter(
                DataValidationRule.entity_type == entity_type,
                DataValidationRule.is_active == True
            )
            .all()
        )

        violations = []
        for rule in rules:
            violation = self._apply_validation_rule(rule, entity_data)
            if violation:
                violations.append(violation)

        return violations

    def _apply_validation_rule(self, rule: DataValidationRule, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply a single validation rule to data."""
        field_value = data.get(rule.field_name)
        config = rule.rule_config

        try:
            if rule.rule_type == "range":
                min_val = config.get("min")
                max_val = config.get("max")
                if field_value is not None:
                    if min_val is not None and field_value < min_val:
                        return self._create_violation(rule, f"Value {field_value} below minimum {min_val}")
                    if max_val is not None and field_value > max_val:
                        return self._create_violation(rule, f"Value {field_value} above maximum {max_val}")

            elif rule.rule_type == "regex":
                pattern = config.get("pattern")
                if field_value is not None and pattern:
                    if not re.match(pattern, str(field_value)):
                        return self._create_violation(rule, f"Value '{field_value}' doesn't match pattern '{pattern}'")

            elif rule.rule_type == "lookup":
                valid_values = config.get("values", [])
                if field_value is not None and field_value not in valid_values:
                    return self._create_violation(rule, f"Value '{field_value}' not in allowed values: {valid_values}")

            elif rule.rule_type == "custom":
                # For custom rules, evaluate the expression
                expression = config.get("expression")
                if expression and field_value is not None:
                    # Simple expression evaluation for common cases
                    if not eval(expression.replace("{value}", str(field_value))):
                        return self._create_violation(rule, f"Custom rule failed: {expression}")

        except Exception as e:
            return self._create_violation(rule, f"Rule evaluation error: {str(e)}")

        return None

    def _create_violation(self, rule: DataValidationRule, message: str) -> Dict[str, Any]:
        """Create a validation violation record."""
        return {
            "rule_id": rule.id,
            "field_name": rule.field_name,
            "rule_type": rule.rule_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Anomaly Detection
    def detect_stat_anomalies(self, game_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect statistical anomalies in player performance."""
        anomalies = []

        # Build query for stat lines
        query = self.db.query(StatLine).join(Player)
        if game_date:
            query = query.filter(StatLine.game_date == game_date)

        stat_lines = query.all()

        for stat_line in stat_lines:
            # Check for extreme values
            if stat_line.points > 50:  # Unusually high points
                anomalies.append(self._create_anomaly_record(
                    entity_type="stat_line",
                    entity_id=str(stat_line.id),
                    anomaly_type="extreme_points",
                    description=f"Player {stat_line.player.full_name} scored {stat_line.points} points in game {stat_line.game_id}",
                    severity="medium"
                ))

            if stat_line.rebounds > 20:  # Unusually high rebounds
                anomalies.append(self._create_anomaly_record(
                    entity_type="stat_line",
                    entity_id=str(stat_line.id),
                    anomaly_type="extreme_rebounds",
                    description=f"Player {stat_line.player.full_name} had {stat_line.rebounds} rebounds in game {stat_line.game_id}",
                    severity="medium"
                ))

            if stat_line.assists > 15:  # Unusually high assists
                anomalies.append(self._create_anomaly_record(
                    entity_type="stat_line",
                    entity_id=str(stat_line.id),
                    anomaly_type="extreme_assists",
                    description=f"Player {stat_line.player.full_name} had {stat_line.assists} assists in game {stat_line.game_id}",
                    severity="medium"
                ))

            # Check for impossible shooting percentages
            if stat_line.field_goal_percentage > 1.0:
                anomalies.append(self._create_anomaly_record(
                    entity_type="stat_line",
                    entity_id=str(stat_line.id),
                    anomaly_type="invalid_percentage",
                    description=f"Player {stat_line.player.full_name} has field goal percentage > 100%: {stat_line.field_goal_percentage}",
                    severity="high"
                ))

        return anomalies

    def detect_data_completeness_issues(self) -> List[Dict[str, Any]]:
        """Detect data completeness issues across the system."""
        issues = []

        # Check for players without positions
        players_no_position = self.db.query(Player).filter(Player.position.is_(None)).count()
        if players_no_position > 0:
            issues.append(self._create_anomaly_record(
                entity_type="player",
                entity_id="multiple",
                anomaly_type="missing_position",
                description=f"{players_no_position} players missing position data",
                severity="medium"
            ))

        # Check for games without scores
        games_no_scores = (
            self.db.query(Game)
            .filter(
                Game.status == "final",
                and_(Game.home_score == 0, Game.away_score == 0)
            )
            .count()
        )
        if games_no_scores > 0:
            issues.append(self._create_anomaly_record(
                entity_type="game",
                entity_id="multiple",
                anomaly_type="missing_scores",
                description=f"{games_no_scores} completed games missing final scores",
                severity="high"
            ))

        # Check for stat lines with zero minutes but positive stats
        impossible_stats = (
            self.db.query(StatLine)
            .filter(
                StatLine.minutes_played == 0,
                StatLine.points > 0
            )
            .count()
        )
        if impossible_stats > 0:
            issues.append(self._create_anomaly_record(
                entity_type="stat_line",
                entity_id="multiple",
                anomaly_type="impossible_stats",
                description=f"{impossible_stats} stat lines with 0 minutes but positive stats",
                severity="high"
            ))

        return issues

    def _create_anomaly_record(
        self,
        entity_type: str,
        entity_id: str,
        anomaly_type: str,
        description: str,
        severity: str
    ) -> Dict[str, Any]:
        """Create an anomaly record for logging."""
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "anomaly_type": anomaly_type,
            "description": description,
            "severity": severity,
            "detected_at": datetime.now(timezone.utc).isoformat()
        }

    def _log_anomaly(
        self,
        entity_type: str,
        entity_id: str,
        anomaly_type: str,
        description: str,
        severity: str
    ) -> DataAnomalyLog:
        """Log an anomaly to the database."""
        anomaly = DataAnomalyLog(
            entity_type=entity_type,
            entity_id=entity_id,
            anomaly_type=anomaly_type,
            description=description,
            severity=severity
        )
        self.db.add(anomaly)
        self.db.commit()
        return anomaly

    # Reporting and Dashboard
    def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data quality dashboard information."""
        # Quality checks summary
        checks_summary = (
            self.db.query(
                DataQualityCheck.status,
                func.count(DataQualityCheck.id).label('count')
            )
            .filter(DataQualityCheck.is_active == True)
            .group_by(DataQualityCheck.status)
            .all()
        )

        # Recent anomalies
        recent_anomalies = (
            self.db.query(DataAnomalyLog)
            .filter(DataAnomalyLog.is_resolved == False)
            .order_by(desc(DataAnomalyLog.detected_at))
            .limit(10)
            .all()
        )

        # Severity breakdown
        severity_breakdown = (
            self.db.query(
                DataAnomalyLog.severity,
                func.count(DataAnomalyLog.id).label('count')
            )
            .filter(DataAnomalyLog.is_resolved == False)
            .group_by(DataAnomalyLog.severity)
            .all()
        )

        return {
            "checks_summary": {row.status: row.count for row in checks_summary},
            "recent_anomalies": [
                {
                    "id": anomaly.id,
                    "entity_type": anomaly.entity_type,
                    "anomaly_type": anomaly.anomaly_type,
                    "description": anomaly.description,
                    "severity": anomaly.severity,
                    "detected_at": anomaly.detected_at.isoformat()
                }
                for anomaly in recent_anomalies
            ],
            "severity_breakdown": {row.severity: row.count for row in severity_breakdown},
            "total_unresolved_anomalies": sum(row.count for row in severity_breakdown)
        }

    def resolve_anomaly(self, anomaly_id: int, resolution_notes: str) -> bool:
        """Mark an anomaly as resolved."""
        anomaly = self.db.query(DataAnomalyLog).filter(DataAnomalyLog.id == anomaly_id).first()
        if not anomaly:
            return False

        anomaly.is_resolved = True
        anomaly.resolved_at = datetime.now(timezone.utc)
        anomaly.resolution_notes = resolution_notes
        self.db.commit()
        return True

    def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get quality trends over the specified number of days."""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Daily anomaly counts
        daily_anomalies = (
            self.db.query(
                func.date(DataAnomalyLog.detected_at).label('date'),
                func.count(DataAnomalyLog.id).label('count')
            )
            .filter(DataAnomalyLog.detected_at >= cutoff_date)
            .group_by(func.date(DataAnomalyLog.detected_at))
            .order_by(func.date(DataAnomalyLog.detected_at))
            .all()
        )

        # Check success rates
        check_success_rates = (
            self.db.query(
                DataQualityCheck.check_name,
                DataQualityCheck.status,
                DataQualityCheck.consecutive_failures
            )
            .filter(DataQualityCheck.is_active == True)
            .all()
        )

        return {
            "daily_anomaly_counts": [
                {"date": row.date.isoformat(), "count": row.count}
                for row in daily_anomalies
            ],
            "check_success_rates": [
                {
                    "name": check.check_name,
                    "status": check.status,
                    "consecutive_failures": check.consecutive_failures
                }
                for check in check_success_rates
            ]
        }