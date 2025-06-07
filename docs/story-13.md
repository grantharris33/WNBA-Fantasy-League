# Story 13: Configure Missing Scheduled Jobs

**Priority**: P1 - Essential Feature  
**Effort**: 1-2 days  
**Dependencies**: None

## Overview
Several important scheduled jobs exist in the codebase but aren't configured in the scheduler. This includes team/standings ingestion, data quality monitoring, and cache cleanup. These jobs are critical for keeping data current and system healthy.

## Acceptance Criteria
1. All necessary jobs are scheduled appropriately
2. Jobs run at optimal times to avoid conflicts
3. Job failures are logged and alerted
4. Jobs can be triggered manually via admin
5. Job status is visible in admin dashboard

## Technical Tasks

### Add Missing Jobs to Scheduler (8 hours)

#### 1. Configure Teams and Standings Jobs (3 hours)
```python
# app/core/scheduler.py - Add these jobs:

# Ingest teams (runs once daily)
scheduler.add_job(
    func=ingest_teams,
    trigger="cron",
    hour=2,
    minute=30,
    id="ingest_teams",
    name="Ingest WNBA Teams",
    misfire_grace_time=3600
)

# Ingest standings (runs every 6 hours during season)
scheduler.add_job(
    func=ingest_standings,
    trigger="cron",
    hour="2,8,14,20",
    minute=45,
    id="ingest_standings", 
    name="Ingest WNBA Standings",
    misfire_grace_time=3600
)

# Update player profiles (runs weekly)
scheduler.add_job(
    func=update_player_profiles,
    trigger="cron",
    day_of_week="tue",
    hour=2,
    minute=0,
    id="update_player_profiles",
    name="Update Player Profiles",
    misfire_grace_time=7200
)
```

#### 2. Configure Data Quality Jobs (2 hours)
```python
# Data quality checks (runs every 4 hours)
scheduler.add_job(
    func=run_data_quality_checks,
    trigger="cron",
    hour="*/4",
    minute=15,
    id="data_quality_checks",
    name="Run Data Quality Checks",
    misfire_grace_time=3600
)

# Clean up old data (runs weekly)
scheduler.add_job(
    func=cleanup_old_data,
    trigger="cron", 
    day_of_week="sun",
    hour=3,
    minute=0,
    id="cleanup_old_data",
    name="Clean Up Old Data",
    misfire_grace_time=7200
)
```

#### 3. Configure Cache and Maintenance Jobs (3 hours)
```python
# Cache cleanup (runs every hour)
scheduler.add_job(
    func=cleanup_expired_cache,
    trigger="cron",
    minute=30,
    id="cache_cleanup",
    name="Clean Expired Cache",
    misfire_grace_time=600
)

# Calculate league analytics (runs daily)
scheduler.add_job(
    func=calculate_league_analytics,
    trigger="cron",
    hour=4,
    minute=30,
    id="league_analytics",
    name="Calculate League Analytics",
    misfire_grace_time=3600
)

# Process notifications queue (runs every 5 minutes)
scheduler.add_job(
    func=process_notification_queue,
    trigger="cron",
    minute="*/5",
    id="process_notifications",
    name="Process Notification Queue",
    misfire_grace_time=60
)
```

### Create Missing Job Functions (8 hours)

#### 1. Implement Data Quality Job (3 hours)
```python
# app/jobs/data_quality_job.py
async def run_data_quality_checks():
    """Run automated data quality checks"""
    checks = [
        check_player_stats_consistency,
        check_roster_slot_integrity,
        check_score_calculation_accuracy,
        check_draft_state_consistency,
    ]
    
    for check in checks:
        try:
            result = await check()
            log_check_result(result)
            if result.has_issues:
                notify_admins(result)
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
```

#### 2. Implement Cleanup Jobs (3 hours)
```python
# app/jobs/maintenance.py
def cleanup_old_data():
    """Clean up old data to manage database size"""
    # Delete old notifications (>30 days)
    # Archive completed leagues (>1 year)
    # Remove orphaned roster slots
    # Clean old ingest logs (>90 days)
    # Vacuum database

def cleanup_expired_cache():
    """Remove expired cache entries"""
    # Clean in-memory cache
    # Clean Redis cache (if configured)
    # Log cache statistics
```

#### 3. Implement Analytics Job (2 hours)
```python
# app/jobs/analytics_job.py  
def calculate_league_analytics():
    """Calculate league-wide analytics"""
    # Calculate league scoring trends
    # Update player consistency scores
    # Calculate trade impact metrics
    # Generate league power rankings
```

### Job Monitoring and Management (4 hours)

#### 1. Add Job Status Tracking (2 hours)
```python
# app/models/__init__.py
class JobExecution(Base):
    __tablename__ = "job_executions"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), nullable=False)
    job_name = Column(String(200))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20))  # running, completed, failed
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
```

#### 2. Add Admin Endpoints (2 hours)
```python
# app/api/admin.py
@router.get("/api/v1/admin/jobs")
def get_scheduled_jobs():
    """List all scheduled jobs and their status"""
    
@router.post("/api/v1/admin/jobs/{job_id}/run")
def trigger_job(job_id: str):
    """Manually trigger a scheduled job"""
    
@router.get("/api/v1/admin/jobs/history")
def get_job_history():
    """Get job execution history"""
```

## Job Schedule Overview

### Daily Jobs
- 2:00 AM - Database backup
- 2:30 AM - Ingest teams
- 3:00 AM - Ingest player stats
- 3:30 AM - Calculate fantasy scores
- 4:00 AM - Calculate analytics
- 4:30 AM - League analytics

### Frequent Jobs
- Every 5 min - Process notifications
- Every 30 min - Cache cleanup
- Every hour - Live game checks (during games)
- Every 4 hours - Data quality checks
- Every 6 hours - Update standings

### Weekly Jobs
- Monday 5:00 AM - Reset weekly moves
- Monday 5:59 AM - Calculate bonuses
- Tuesday 2:00 AM - Update player profiles
- Sunday 3:00 AM - Data cleanup

## Error Handling
- All jobs wrapped in try/catch
- Errors logged with full context
- Critical failures trigger admin alerts
- Jobs can retry with backoff
- Misfire grace time prevents pile-up

## Testing Requirements
- [ ] Test all job functions individually
- [ ] Test job scheduling configuration
- [ ] Test manual job triggering
- [ ] Test error handling and recovery
- [ ] Test job status tracking

## Monitoring
- Job execution history visible in admin
- Failed jobs trigger notifications
- Long-running jobs logged
- Resource usage tracked
- Schedule conflicts detected

## Definition of Done
- All jobs scheduled appropriately
- Jobs run successfully on schedule
- Manual triggering works
- Errors are handled gracefully
- Admin can monitor job status
- No job conflicts or pile-ups
- Documentation updated