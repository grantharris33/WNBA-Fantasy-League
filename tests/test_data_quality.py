import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy import text

from app.services.data_quality import DataQualityService
from app.models import DataQualityCheck, DataValidationRule, DataAnomalyLog, Player, StatLine


class TestDataQualityService:
    """Test the DataQualityService class."""
    
    def test_create_quality_check(self, db):
        """Test creating a quality check."""
        service = DataQualityService(db)
        
        check = service.create_quality_check(
            check_name="Test Check",
            check_type="completeness",
            target_table="player",
            check_query="SELECT COUNT(*) FROM player WHERE position IS NULL",
            expected_result="0",
            failure_threshold=1
        )
        
        assert check.check_name == "Test Check"
        assert check.check_type == "completeness"
        assert check.target_table == "player"
        assert check.status == "pending"
        assert check.is_active is True
    
    def test_create_validation_rule(self, db):
        """Test creating a validation rule."""
        service = DataQualityService(db)
        
        rule = service.create_validation_rule(
            entity_type="stat_line",
            field_name="points",
            rule_type="range",
            rule_config={"min": 0, "max": 100}
        )
        
        assert rule.entity_type == "stat_line"
        assert rule.field_name == "points"
        assert rule.rule_type == "range"
        assert rule.rule_config == {"min": 0, "max": 100}
        assert rule.is_active is True
    
    def test_validate_entity_range_rule(self, db):
        """Test entity validation with range rule."""
        service = DataQualityService(db)
        
        # Create a range rule
        rule = service.create_validation_rule(
            entity_type="stat_line",
            field_name="points",
            rule_type="range",
            rule_config={"min": 0, "max": 50}
        )
        
        # Test valid data
        valid_data = {"points": 25}
        violations = service.validate_entity("stat_line", valid_data)
        assert len(violations) == 0
        
        # Test invalid data (too high)
        invalid_data = {"points": 75}
        violations = service.validate_entity("stat_line", invalid_data)
        assert len(violations) == 1
        assert "above maximum" in violations[0]["message"]
        
        # Test invalid data (too low)
        invalid_data = {"points": -5}
        violations = service.validate_entity("stat_line", invalid_data)
        assert len(violations) == 1
        assert "below minimum" in violations[0]["message"]
    
    def test_validate_entity_lookup_rule(self, db):
        """Test entity validation with lookup rule."""
        service = DataQualityService(db)
        
        # Create a lookup rule
        rule = service.create_validation_rule(
            entity_type="player",
            field_name="position",
            rule_type="lookup",
            rule_config={"values": ["G", "F", "C"]}
        )
        
        # Test valid data
        valid_data = {"position": "G"}
        violations = service.validate_entity("player", valid_data)
        assert len(violations) == 0
        
        # Test invalid data
        invalid_data = {"position": "XYZ"}
        violations = service.validate_entity("player", invalid_data)
        assert len(violations) == 1
        assert "not in allowed values" in violations[0]["message"]
    
    def test_run_quality_check_success(self, db):
        """Test running a quality check that passes."""
        service = DataQualityService(db)
        
        # Create a simple check that should pass
        check = service.create_quality_check(
            check_name="Count Check",
            check_type="completeness",
            target_table="user",
            check_query="SELECT 5",  # Simple query that returns 5
            expected_result=None,  # Any result is fine
            failure_threshold=1
        )
        db.commit()  # Commit to get the ID
        
        # Run the check (it will actually execute against the test database)
        success = service.run_quality_check(check.id)
        
        # Refresh the check to get updated values
        db.refresh(check)
        
        assert success is True
        assert check.status == "passed"
        assert check.last_result == "5"
        assert check.consecutive_failures == 0
    
    def test_run_quality_check_failure(self, db):
        """Test running a quality check that fails."""
        service = DataQualityService(db)
        
        # Create a check with specific expected result
        check = service.create_quality_check(
            check_name="Specific Count Check",
            check_type="completeness",
            target_table="user",
            check_query="SELECT 2",  # Returns 2
            expected_result="0",  # But we expect 0
            failure_threshold=1
        )
        db.commit()  # Commit to get the ID
        
        # Run the check (it will fail because 2 != 0)
        success = service.run_quality_check(check.id)
        
        # Refresh the check to get updated values
        db.refresh(check)
        
        assert success is False
        assert check.status == "failed"
        assert check.last_result == "2"
        assert check.consecutive_failures == 1
    
    def test_detect_stat_anomalies(self, db):
        """Test statistical anomaly detection."""
        service = DataQualityService(db)
        
        # Create test data
        player = Player(id=1, full_name="Test Player", position="G")
        db.add(player)
        
        # Create stat line with extreme values
        extreme_stat = StatLine(
            id=1,
            player_id=1,
            game_id="test_game",
            game_date=datetime.now(timezone.utc),
            points=75,  # Extreme value
            rebounds=25,  # Extreme value
            assists=20,  # Extreme value
            field_goal_percentage=1.5  # Invalid value > 100%
        )
        db.add(extreme_stat)
        db.commit()
        
        anomalies = service.detect_stat_anomalies()
        
        # Should detect multiple anomalies for this stat line
        assert len(anomalies) >= 4  # points, rebounds, assists, field_goal_percentage
        
        anomaly_types = [a["anomaly_type"] for a in anomalies]
        assert "extreme_points" in anomaly_types
        assert "extreme_rebounds" in anomaly_types
        assert "extreme_assists" in anomaly_types
        assert "invalid_percentage" in anomaly_types
    
    def test_detect_data_completeness_issues(self, db):
        """Test data completeness issue detection."""
        service = DataQualityService(db)
        
        # Create test data with missing information
        player = Player(id=1, full_name="Test Player", position=None)  # Missing position
        db.add(player)
        db.commit()
        
        issues = service.detect_data_completeness_issues()
        
        # Should detect the missing position issue
        issue_types = [i["anomaly_type"] for i in issues]
        assert "missing_position" in issue_types
    
    def test_resolve_anomaly(self, db):
        """Test resolving an anomaly."""
        service = DataQualityService(db)
        
        # Create an anomaly
        anomaly = service._log_anomaly(
            entity_type="test",
            entity_id="test_id",
            anomaly_type="test_anomaly",
            description="Test anomaly",
            severity="medium"
        )
        
        assert anomaly.is_resolved is False
        
        # Resolve the anomaly
        success = service.resolve_anomaly(anomaly.id, "Resolved for testing")
        
        assert success is True
        assert anomaly.is_resolved is True
        assert anomaly.resolution_notes == "Resolved for testing"
        assert anomaly.resolved_at is not None
    
    def test_get_quality_dashboard_data(self, db):
        """Test getting dashboard data."""
        service = DataQualityService(db)
        
        # Create some test data
        check = service.create_quality_check(
            check_name="Test Check",
            check_type="completeness",
            target_table="player",
            check_query="SELECT 1",
            expected_result="1"
        )
        check.status = "passed"
        
        anomaly = service._log_anomaly(
            entity_type="test",
            entity_id="test_id",
            anomaly_type="test_anomaly",
            description="Test anomaly",
            severity="high"
        )
        
        dashboard_data = service.get_quality_dashboard_data()
        
        assert "checks_summary" in dashboard_data
        assert "recent_anomalies" in dashboard_data
        assert "severity_breakdown" in dashboard_data
        assert "total_unresolved_anomalies" in dashboard_data
        
        assert dashboard_data["checks_summary"]["passed"] == 1
        assert dashboard_data["severity_breakdown"]["high"] == 1
        assert dashboard_data["total_unresolved_anomalies"] == 1