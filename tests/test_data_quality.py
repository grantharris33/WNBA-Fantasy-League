import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.services.data_quality import DataQualityService
from app.models import DataQualityCheck, DataValidationRule, DataAnomalyLog, Player, StatLine


class TestDataQualityService:
    """Test the DataQualityService class."""
    
    def test_create_quality_check(self, db_session):
        """Test creating a quality check."""
        service = DataQualityService(db_session)
        
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
    
    def test_create_validation_rule(self, db_session):
        """Test creating a validation rule."""
        service = DataQualityService(db_session)
        
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
    
    def test_validate_entity_range_rule(self, db_session):
        """Test entity validation with range rule."""
        service = DataQualityService(db_session)
        
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
    
    def test_validate_entity_lookup_rule(self, db_session):
        """Test entity validation with lookup rule."""
        service = DataQualityService(db_session)
        
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
    
    def test_run_quality_check_success(self, db_session):
        """Test running a quality check that passes."""
        service = DataQualityService(db_session)
        
        # Create a simple check that should pass
        check = service.create_quality_check(
            check_name="Count Check",
            check_type="completeness",
            target_table="user",
            check_query="SELECT COUNT(*) FROM user",
            expected_result=None,  # Any result is fine
            failure_threshold=1
        )
        
        # Mock the database execution
        with patch.object(db_session, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.scalar.return_value = 5
            mock_result.returns_rows = True
            mock_execute.return_value = mock_result
            
            success = service.run_quality_check(check.id)
            
            assert success is True
            assert check.status == "passed"
            assert check.last_result == "5"
            assert check.consecutive_failures == 0
    
    def test_run_quality_check_failure(self, db_session):
        """Test running a quality check that fails."""
        service = DataQualityService(db_session)
        
        # Create a check with specific expected result
        check = service.create_quality_check(
            check_name="Specific Count Check",
            check_type="completeness",
            target_table="user",
            check_query="SELECT COUNT(*) FROM user WHERE is_admin = 1",
            expected_result="0",
            failure_threshold=1
        )
        
        # Mock the database execution to return unexpected result
        with patch.object(db_session, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.scalar.return_value = 2
            mock_result.returns_rows = True
            mock_execute.return_value = mock_result
            
            success = service.run_quality_check(check.id)
            
            assert success is False
            assert check.status == "failed"
            assert check.last_result == "2"
            assert check.consecutive_failures == 1
    
    def test_detect_stat_anomalies(self, db_session):
        """Test statistical anomaly detection."""
        service = DataQualityService(db_session)
        
        # Create test data
        player = Player(id=1, full_name="Test Player", position="G")
        db_session.add(player)
        
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
        db_session.add(extreme_stat)
        db_session.commit()
        
        anomalies = service.detect_stat_anomalies()
        
        # Should detect multiple anomalies for this stat line
        assert len(anomalies) >= 4  # points, rebounds, assists, field_goal_percentage
        
        anomaly_types = [a["anomaly_type"] for a in anomalies]
        assert "extreme_points" in anomaly_types
        assert "extreme_rebounds" in anomaly_types
        assert "extreme_assists" in anomaly_types
        assert "invalid_percentage" in anomaly_types
    
    def test_detect_data_completeness_issues(self, db_session):
        """Test data completeness issue detection."""
        service = DataQualityService(db_session)
        
        # Create test data with missing information
        player = Player(id=1, full_name="Test Player", position=None)  # Missing position
        db_session.add(player)
        db_session.commit()
        
        issues = service.detect_data_completeness_issues()
        
        # Should detect the missing position issue
        issue_types = [i["anomaly_type"] for i in issues]
        assert "missing_position" in issue_types
    
    def test_resolve_anomaly(self, db_session):
        """Test resolving an anomaly."""
        service = DataQualityService(db_session)
        
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
    
    def test_get_quality_dashboard_data(self, db_session):
        """Test getting dashboard data."""
        service = DataQualityService(db_session)
        
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