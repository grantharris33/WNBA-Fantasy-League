from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models import Team, User
from app.services.admin import AdminService
from app.services.data_quality import DataQualityService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# Pydantic schemas for admin endpoints
from pydantic import BaseModel


class ModifyLineupRequest(BaseModel):
    starter_ids: List[int]
    justification: str = ""


class RecalculateScoreRequest(BaseModel):
    justification: str = ""


class GrantMovesRequest(BaseModel):
    additional_moves: int
    justification: str = ""


class AdminActionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


class NewGrantMovesRequest(BaseModel):
    moves_to_grant: int
    reason: str
    week_id: int


class ForceSetRosterRequest(BaseModel):
    starter_ids: List[int]
    week_id: int
    bypass_move_limit: bool = True


class TeamMoveSummaryResponse(BaseModel):
    team_id: int
    week_id: int
    base_moves: int
    admin_granted_moves: int
    total_available_moves: int
    moves_used: int
    moves_remaining: int
    admin_grants: List[Dict]


class AdminMoveGrantResponse(BaseModel):
    id: int
    team_id: int
    admin_user_id: int
    moves_granted: int
    reason: str
    granted_at: str
    week_id: int


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    admin_email: str
    action: str
    details: str
    path: Optional[str] = None
    method: Optional[str] = None


class LineupHistoryEntry(BaseModel):
    week_id: int
    lineup: List[Dict]
    admin_modified: bool
    modification_count: int
    last_modified: Optional[str] = None


# Data Quality Schemas
class CreateQualityCheckRequest(BaseModel):
    check_name: str
    check_type: str  # completeness, accuracy, consistency
    target_table: str
    check_query: str
    expected_result: Optional[str] = None
    failure_threshold: int = 1


class CreateValidationRuleRequest(BaseModel):
    entity_type: str  # player, game, stat_line
    field_name: str
    rule_type: str  # range, regex, lookup, custom
    rule_config: Dict


class QualityCheckResponse(BaseModel):
    id: int
    check_name: str
    check_type: str
    target_table: str
    status: str
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    consecutive_failures: int
    is_active: bool


class ValidationRuleResponse(BaseModel):
    id: int
    entity_type: str
    field_name: str
    rule_type: str
    rule_config: Dict
    is_active: bool


class AnomalyResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    anomaly_type: str
    description: str
    severity: str
    detected_at: str
    is_resolved: bool
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None


class QualityDashboardResponse(BaseModel):
    checks_summary: Dict[str, int]
    recent_anomalies: List[Dict]
    severity_breakdown: Dict[str, int]
    total_unresolved_anomalies: int


class ResolveAnomalyRequest(BaseModel):
    resolution_notes: str


@router.put("/teams/{team_id}/lineups/{week_id}")
async def modify_historical_lineup(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    request: ModifyLineupRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Modify historical lineup for a team and week.
    Requires admin privileges.
    """
    try:
        admin_service = AdminService(db)

        success = admin_service.modify_historical_lineup(
            team_id=team_id,
            week_id=week_id,
            changes={"starter_ids": request.starter_ids},
            admin_user_id=current_user.id,
            justification=request.justification,
        )

        if success:
            return AdminActionResponse(
                success=True,
                message=f"Successfully modified lineup for team {team_id}, week {week_id}",
                data={"team_id": team_id, "week_id": week_id, "starter_ids": request.starter_ids},
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to modify lineup")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/teams/{team_id}/weeks/{week_id}/recalculate")
async def recalculate_team_week_score(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    request: RecalculateScoreRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Recalculate score for a specific team and week.
    Requires admin privileges.
    """
    try:
        admin_service = AdminService(db)

        new_score = admin_service.recalculate_team_week_score(
            team_id=team_id, week_id=week_id, admin_user_id=current_user.id, justification=request.justification
        )

        if new_score is not None:
            return AdminActionResponse(
                success=True,
                message=f"Successfully recalculated score for team {team_id}, week {week_id}",
                data={"team_id": team_id, "week_id": week_id, "new_score": new_score},
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to recalculate score")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/teams/{team_id}/moves/grant")
async def grant_additional_moves(
    team_id: int = Path(..., description="Team ID"),
    request: GrantMovesRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Grant additional weekly moves to a team.
    Requires admin privileges.
    """
    try:
        admin_service = AdminService(db)

        success = admin_service.override_weekly_moves(
            team_id=team_id,
            additional_moves=request.additional_moves,
            admin_user_id=current_user.id,
            justification=request.justification,
        )

        if success:
            return AdminActionResponse(
                success=True,
                message=f"Successfully granted {request.additional_moves} additional moves to team {team_id}",
                data={"team_id": team_id, "additional_moves": request.additional_moves},
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to grant additional moves")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/audit-log")
async def get_admin_audit_log(
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> List[AuditLogEntry]:
    """
    Get admin action audit log.
    Requires admin privileges.
    """
    try:
        admin_service = AdminService(db)

        logs = admin_service.get_admin_audit_log(team_id=team_id, limit=limit, offset=offset)

        return [AuditLogEntry(**log) for log in logs]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/teams/{team_id}/lineup-history")
async def get_team_lineup_history(
    team_id: int = Path(..., description="Team ID"),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> List[LineupHistoryEntry]:
    """
    Get lineup history for a team with admin modification indicators.
    Requires admin privileges.
    """
    try:
        admin_service = AdminService(db)

        history = admin_service.get_team_lineup_history(team_id)

        return [LineupHistoryEntry(**entry) for entry in history]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/teams/{team_id}/weeks/{week_id}/lineup")
async def get_admin_lineup_view(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> Dict:
    """
    Get detailed lineup view for admin modification.
    Includes all players on roster and current starter status.
    """
    try:
        admin_service = AdminService(db)

        lineup = admin_service.lineup_service.get_weekly_lineup(team_id, week_id)
        if not lineup:
            raise HTTPException(status_code=404, detail="Lineup not found")

        # Check if lineup has been admin-modified
        history = admin_service.get_team_lineup_history(team_id)
        week_entry = next((entry for entry in history if entry["week_id"] == week_id), None)

        return {
            "team_id": team_id,
            "week_id": week_id,
            "lineup": lineup,
            "admin_modified": week_entry["admin_modified"] if week_entry else False,
            "modification_count": week_entry["modification_count"] if week_entry else 0,
            "last_modified": week_entry["last_modified"] if week_entry else None,
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# New endpoints for Story 3: Enhanced Admin Move Management


@router.post("/teams/{team_id}/weeks/{week_id}/grant-moves")
async def grant_team_moves(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    request: NewGrantMovesRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminMoveGrantResponse:
    """
    Grant additional moves to a team for a specific week.
    Requires admin privileges.
    """
    try:
        from app.services.roster import RosterService

        roster_service = RosterService(db)

        grant = roster_service.grant_admin_moves(
            team_id=team_id,
            week_id=week_id,
            moves_to_grant=request.moves_to_grant,
            reason=request.reason,
            admin_user_id=current_user.id,
        )

        return AdminMoveGrantResponse(
            id=grant.id,
            team_id=grant.team_id,
            admin_user_id=grant.admin_user_id,
            moves_granted=grant.moves_granted,
            reason=grant.reason,
            granted_at=grant.granted_at.isoformat(),
            week_id=grant.week_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/teams/{team_id}/weeks/{week_id}/move-summary")
async def get_team_move_summary(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> TeamMoveSummaryResponse:
    """
    Get detailed move summary for a team including admin grants.
    Requires admin privileges.
    """
    try:
        from app.services.roster import RosterService

        roster_service = RosterService(db)

        summary = roster_service.get_team_move_summary(team_id, week_id)

        return TeamMoveSummaryResponse(**summary)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/teams/{team_id}/weeks/{week_id}/force-roster")
async def force_set_team_roster(
    team_id: int = Path(..., description="Team ID"),
    week_id: int = Path(..., description="Week ID"),
    request: ForceSetRosterRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Force set team roster with admin override, bypassing move limits.
    Requires admin privileges.
    """
    try:
        from app.services.roster import RosterService

        roster_service = RosterService(db)

        starters = roster_service.set_starters_admin_override(
            team_id=team_id,
            starter_player_ids=request.starter_ids,
            admin_user_id=current_user.id,
            week_id=week_id,
            bypass_move_limit=request.bypass_move_limit,
        )

        return AdminActionResponse(
            success=True,
            message=f"Successfully set roster for team {team_id}, week {week_id}",
            data={
                "team_id": team_id,
                "week_id": week_id,
                "starter_ids": request.starter_ids,
                "bypass_move_limit": request.bypass_move_limit,
                "starters_count": len(starters),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Data Quality Management Endpoints


@router.get("/data-quality/dashboard")
async def get_data_quality_dashboard(
    current_user: Annotated[User, Depends(get_admin_user)] = None, db: Annotated[Session, Depends(get_db)] = None
) -> QualityDashboardResponse:
    """
    Get data quality dashboard overview.
    Requires admin privileges.
    """
    try:
        quality_service = DataQualityService(db)
        dashboard_data = quality_service.get_quality_dashboard_data()
        return QualityDashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data-quality/checks")
async def create_quality_check(
    request: CreateQualityCheckRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> QualityCheckResponse:
    """
    Create a new data quality check.
    Requires admin privileges.
    """
    try:
        quality_service = DataQualityService(db)
        check = quality_service.create_quality_check(
            check_name=request.check_name,
            check_type=request.check_type,
            target_table=request.target_table,
            check_query=request.check_query,
            expected_result=request.expected_result,
            failure_threshold=request.failure_threshold,
        )

        return QualityCheckResponse(
            id=check.id,
            check_name=check.check_name,
            check_type=check.check_type,
            target_table=check.target_table,
            status=check.status,
            last_run=check.last_run.isoformat() if check.last_run else None,
            last_result=check.last_result,
            consecutive_failures=check.consecutive_failures,
            is_active=check.is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data-quality/checks")
async def list_quality_checks(
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    active_only: bool = Query(True, description="Filter to active checks only"),
) -> List[QualityCheckResponse]:
    """
    List all data quality checks.
    Requires admin privileges.
    """
    try:
        from app.models import DataQualityCheck

        query = db.query(DataQualityCheck)
        if active_only:
            query = query.filter(DataQualityCheck.is_active == True)

        checks = query.all()

        return [
            QualityCheckResponse(
                id=check.id,
                check_name=check.check_name,
                check_type=check.check_type,
                target_table=check.target_table,
                status=check.status,
                last_run=check.last_run.isoformat() if check.last_run else None,
                last_result=check.last_result,
                consecutive_failures=check.consecutive_failures,
                is_active=check.is_active,
            )
            for check in checks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data-quality/checks/{check_id}/run")
async def run_quality_check(
    check_id: int = Path(..., description="Quality check ID"),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Run a specific data quality check.
    Requires admin privileges.
    """
    try:
        quality_service = DataQualityService(db)
        success = quality_service.run_quality_check(check_id)

        return AdminActionResponse(
            success=success,
            message=f"Quality check {check_id} executed successfully"
            if success
            else f"Quality check {check_id} failed",
            data={"check_id": check_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data-quality/checks/run-all")
async def run_all_quality_checks(
    current_user: Annotated[User, Depends(get_admin_user)] = None, db: Annotated[Session, Depends(get_db)] = None
) -> AdminActionResponse:
    """
    Run all active data quality checks.
    Requires admin privileges.
    """
    try:
        quality_service = DataQualityService(db)
        results = quality_service.run_all_quality_checks()

        return AdminActionResponse(
            success=True, message=f"Ran {len(results)} quality checks", data={"results": results}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data-quality/anomalies")
async def list_anomalies(
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    unresolved_only: bool = Query(True, description="Filter to unresolved anomalies only"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
) -> List[AnomalyResponse]:
    """
    List data quality anomalies.
    Requires admin privileges.
    """
    try:
        from app.models import DataQualityAnomaly

        query = db.query(DataQualityAnomaly)
        if unresolved_only:
            query = query.filter(DataQualityAnomaly.is_resolved == False)
        if severity:
            query = query.filter(DataQualityAnomaly.severity == severity)

        query = query.order_by(desc(DataQualityAnomaly.detected_at))
        anomalies = query.limit(limit).all()

        return [
            AnomalyResponse(
                id=anomaly.id,
                entity_type=anomaly.entity_type,
                entity_id=str(anomaly.entity_id),
                anomaly_type=anomaly.anomaly_type,
                description=anomaly.description,
                severity=anomaly.severity,
                detected_at=anomaly.detected_at.isoformat(),
                is_resolved=anomaly.is_resolved,
                resolved_at=anomaly.resolved_at.isoformat() if anomaly.resolved_at else None,
                resolution_notes=anomaly.resolution_notes,
            )
            for anomaly in anomalies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/data-quality/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: int = Path(..., description="Anomaly ID"),
    request: ResolveAnomalyRequest = Body(...),
    current_user: Annotated[User, Depends(get_admin_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> AdminActionResponse:
    """
    Resolve a data quality anomaly.
    Requires admin privileges.
    """
    try:
        quality_service = DataQualityService(db)
        success = quality_service.resolve_anomaly(anomaly_id, request.resolution_notes)

        return AdminActionResponse(
            success=success,
            message=f"Anomaly {anomaly_id} resolved successfully"
            if success
            else f"Failed to resolve anomaly {anomaly_id}",
            data={"anomaly_id": anomaly_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/system-stats")
async def get_system_stats(
    current_user: Annotated[User, Depends(get_admin_user)] = None, db: Annotated[Session, Depends(get_db)] = None
) -> Dict:
    """
    Get system statistics for admin dashboard.
    Requires admin privileges.
    """
    try:
        from app.models import League, Team, User

        # Get basic counts
        total_users = db.query(User).count()
        total_teams = db.query(Team).count()
        total_leagues = db.query(League).count()

        # Get quality issues count
        quality_service = DataQualityService(db)
        dashboard_data = quality_service.get_quality_dashboard_data()
        active_data_issues = dashboard_data.get("total_unresolved_anomalies", 0)

        # Get last ingest time from audit logs
        admin_service = AdminService(db)
        recent_logs = admin_service.get_admin_audit_log(limit=1)
        last_ingest_time = recent_logs[0]["timestamp"] if recent_logs else None

        return {
            "totalUsers": total_users,
            "totalTeams": total_teams,
            "totalLeagues": total_leagues,
            "activeDataIssues": active_data_issues,
            "lastIngestTime": last_ingest_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/teams")
async def list_teams(
    current_user: Annotated[User, Depends(get_admin_user)] = None, db: Annotated[Session, Depends(get_db)] = None
) -> List[Dict]:
    """
    List all teams for admin management.
    Requires admin privileges.
    """
    try:
        from app.models import League

        teams = (
            db.query(Team, User.email, League.name)
            .join(User, Team.owner_id == User.id)
            .join(League, Team.league_id == League.id)
            .all()
        )

        return [
            {
                "id": team.id,
                "name": team.name,
                "owner_email": owner_email,
                "moves_this_week": team.moves_this_week,
                "league_name": league_name,
            }
            for team, owner_email, league_name in teams
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
