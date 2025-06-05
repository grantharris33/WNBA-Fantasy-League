from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.database import SessionLocal
from app.models import IngestLog
from app.services.data_quality import DataQualityService


async def run_daily_quality_checks() -> Dict[str, Any]:
    """
    Run all active quality checks on a daily schedule.
    Typically scheduled to run after daily data ingestion.
    """
    session = SessionLocal()
    try:
        quality_service = DataQualityService(session)

        _log_info("Starting daily quality checks")

        # Run all active quality checks
        results = quality_service.run_all_active_checks()

        # Log summary
        _log_info(
            f"Daily quality checks completed: {results['passed']} passed, {results['failed']} failed, {results['errors']} errors"
        )

        # If there are failures, run anomaly detection
        if results['failed'] > 0 or results['errors'] > 0:
            _log_info("Running additional anomaly detection due to check failures")
            await run_anomaly_detection()

        return results

    except Exception as e:
        _log_error(f"Daily quality checks failed: {str(e)}")
        raise
    finally:
        session.close()


async def run_anomaly_detection(game_date: str | None = None) -> Dict[str, Any]:
    """
    Run comprehensive anomaly detection.
    Can be scheduled independently or triggered by quality check failures.
    """
    session = SessionLocal()
    try:
        quality_service = DataQualityService(session)

        _log_info(f"Starting anomaly detection for {game_date or 'all recent data'}")

        # Detect statistical anomalies
        stat_anomalies = quality_service.detect_stat_anomalies(game_date)

        # Detect data completeness issues
        completeness_issues = quality_service.detect_data_completeness_issues()

        # Log detected anomalies
        for anomaly in stat_anomalies:
            quality_service._log_anomaly(
                entity_type=anomaly["entity_type"],
                entity_id=anomaly["entity_id"],
                anomaly_type=anomaly["anomaly_type"],
                description=anomaly["description"],
                severity=anomaly["severity"],
            )

        for anomaly in completeness_issues:
            quality_service._log_anomaly(
                entity_type=anomaly["entity_type"],
                entity_id=anomaly["entity_id"],
                anomaly_type=anomaly["anomaly_type"],
                description=anomaly["description"],
                severity=anomaly["severity"],
            )

        total_detected = len(stat_anomalies) + len(completeness_issues)
        _log_info(f"Anomaly detection completed: {total_detected} anomalies detected")

        return {
            "stat_anomalies": stat_anomalies,
            "completeness_issues": completeness_issues,
            "total_detected": total_detected,
        }

    except Exception as e:
        _log_error(f"Anomaly detection failed: {str(e)}")
        raise
    finally:
        session.close()


async def create_default_quality_checks() -> None:
    """
    Create default quality checks for the system.
    Should be run once during system setup.
    """
    session = SessionLocal()
    try:
        quality_service = DataQualityService(session)

        _log_info("Creating default quality checks")

        # Data completeness checks
        default_checks = [
            {
                "check_name": "Player Position Completeness",
                "check_type": "completeness",
                "target_table": "player",
                "check_query": "SELECT COUNT(*) FROM player WHERE position IS NULL",
                "expected_result": "0",
                "failure_threshold": 1,
            },
            {
                "check_name": "Game Score Completeness",
                "check_type": "completeness",
                "target_table": "game",
                "check_query": "SELECT COUNT(*) FROM game WHERE status = 'final' AND (home_score = 0 AND away_score = 0)",
                "expected_result": "0",
                "failure_threshold": 1,
            },
            {
                "check_name": "Stat Line Consistency",
                "check_type": "consistency",
                "target_table": "stat_line",
                "check_query": "SELECT COUNT(*) FROM stat_line WHERE minutes_played = 0 AND points > 0",
                "expected_result": "0",
                "failure_threshold": 5,
            },
            {
                "check_name": "Shooting Percentage Accuracy",
                "check_type": "accuracy",
                "target_table": "stat_line",
                "check_query": "SELECT COUNT(*) FROM stat_line WHERE field_goal_percentage > 1.0",
                "expected_result": "0",
                "failure_threshold": 1,
            },
            {
                "check_name": "Recent Data Freshness",
                "check_type": "completeness",
                "target_table": "stat_line",
                "check_query": "SELECT COUNT(*) FROM stat_line WHERE game_date >= DATE('now', '-2 days')",
                "expected_result": None,  # Variable based on schedule
                "failure_threshold": 1,
            },
        ]

        # Create validation rules
        default_rules = [
            {
                "entity_type": "stat_line",
                "field_name": "points",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 100},
            },
            {
                "entity_type": "stat_line",
                "field_name": "rebounds",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 50},
            },
            {
                "entity_type": "stat_line",
                "field_name": "assists",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 30},
            },
            {
                "entity_type": "stat_line",
                "field_name": "field_goal_percentage",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 1.0},
            },
            {
                "entity_type": "stat_line",
                "field_name": "three_point_percentage",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 1.0},
            },
            {
                "entity_type": "stat_line",
                "field_name": "free_throw_percentage",
                "rule_type": "range",
                "rule_config": {"min": 0, "max": 1.0},
            },
            {
                "entity_type": "player",
                "field_name": "position",
                "rule_type": "lookup",
                "rule_config": {"values": ["G", "F", "C", "PG", "SG", "SF", "PF"]},
            },
        ]

        # Create checks
        created_checks = 0
        for check_config in default_checks:
            try:
                quality_service.create_quality_check(**check_config)
                created_checks += 1
            except Exception as e:
                _log_error(f"Failed to create quality check '{check_config['check_name']}': {str(e)}")

        # Create validation rules
        created_rules = 0
        for rule_config in default_rules:
            try:
                quality_service.create_validation_rule(**rule_config)
                created_rules += 1
            except Exception as e:
                _log_error(
                    f"Failed to create validation rule for {rule_config['entity_type']}.{rule_config['field_name']}: {str(e)}"
                )

        _log_info(f"Default setup completed: {created_checks} quality checks, {created_rules} validation rules created")

    except Exception as e:
        _log_error(f"Failed to create default quality checks: {str(e)}")
        raise
    finally:
        session.close()


async def cleanup_old_anomalies(days_to_keep: int = 30) -> int:
    """
    Clean up old resolved anomalies to prevent database bloat.
    """
    session = SessionLocal()
    try:
        from datetime import timedelta

        from app.models import DataAnomalyLog

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # Delete old resolved anomalies
        deleted_count = (
            session.query(DataAnomalyLog)
            .filter(DataAnomalyLog.is_resolved == True, DataAnomalyLog.resolved_at < cutoff_date)
            .delete()
        )

        session.commit()
        _log_info(f"Cleaned up {deleted_count} old resolved anomalies")

        return deleted_count

    except Exception as e:
        session.rollback()
        _log_error(f"Failed to cleanup old anomalies: {str(e)}")
        raise
    finally:
        session.close()


def _log_info(msg: str) -> None:
    """Log an info message to the database."""
    session = SessionLocal()
    try:
        ingest_log = IngestLog(provider="data_quality", message=f"INFO: {msg}")
        session.add(ingest_log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _log_error(msg: str) -> None:
    """Log an error message to the database."""
    session = SessionLocal()
    try:
        ingest_log = IngestLog(provider="data_quality", message=f"ERROR: {msg}")
        session.add(ingest_log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


# Entry points for scheduler
async def main_daily_quality_check():
    """Main entry point for daily quality check job."""
    try:
        await run_daily_quality_checks()
    except Exception as e:
        _log_error(f"Daily quality check job failed: {str(e)}")


async def main_anomaly_detection():
    """Main entry point for anomaly detection job."""
    try:
        await run_anomaly_detection()
    except Exception as e:
        _log_error(f"Anomaly detection job failed: {str(e)}")


async def main_cleanup():
    """Main entry point for cleanup job."""
    try:
        await cleanup_old_anomalies()
    except Exception as e:
        _log_error(f"Cleanup job failed: {str(e)}")


if __name__ == "__main__":
    # For testing purposes
    asyncio.run(create_default_quality_checks())
