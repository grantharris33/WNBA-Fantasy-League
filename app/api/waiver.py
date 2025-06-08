"""Waiver wire API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import WaiverClaimCreateRequest, WaiverClaimResponse, WaiverPlayerResponse, WaiverPriorityResponse
from app.models import User
from app.services.waiver import WaiverService

router = APIRouter()


@router.get("/leagues/{league_id}/waivers", response_model=list[WaiverPlayerResponse])
def get_waiver_wire_players(
    league_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[WaiverPlayerResponse]:
    """Get all players currently on waivers for a league."""
    waiver_service = WaiverService(db)

    try:
        players = waiver_service.get_waiver_wire_players(league_id)

        return [
            WaiverPlayerResponse(
                id=player.id,
                full_name=player.full_name,
                position=player.position,
                team_abbr=player.team_abbr,
                waiver_expires_at=player.waiver_expires_at,
                is_on_waivers=True,
            )
            for player in players
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching waiver wire: {str(e)}")


@router.get("/teams/{team_id}/waiver-claims", response_model=list[WaiverClaimResponse])
def get_team_waiver_claims(
    team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[WaiverClaimResponse]:
    """Get all waiver claims for a team."""
    waiver_service = WaiverService(db)

    try:
        claims = waiver_service.get_team_claims(team_id)

        return [
            WaiverClaimResponse(
                id=claim.id,
                team_id=claim.team_id,
                player_id=claim.player_id,
                player_name=claim.player.full_name if claim.player else "Unknown",
                player_position=claim.player.position if claim.player else None,
                drop_player_id=claim.drop_player_id,
                drop_player_name=claim.drop_player.full_name if claim.drop_player else None,
                priority=claim.priority,
                status=claim.status,
                created_at=claim.created_at,
                processed_at=claim.processed_at,
            )
            for claim in claims
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching waiver claims: {str(e)}")


@router.post("/teams/{team_id}/waiver-claims", response_model=WaiverClaimResponse)
def submit_waiver_claim(
    team_id: int,
    request: WaiverClaimCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaiverClaimResponse:
    """Submit a waiver claim for a player."""
    waiver_service = WaiverService(db)

    try:
        claim = waiver_service.submit_claim(
            team_id=team_id,
            player_id=request.player_id,
            drop_player_id=request.drop_player_id,
            priority=request.priority,
        )

        return WaiverClaimResponse(
            id=claim.id,
            team_id=claim.team_id,
            player_id=claim.player_id,
            player_name=claim.player.full_name if claim.player else "Unknown",
            player_position=claim.player.position if claim.player else None,
            drop_player_id=claim.drop_player_id,
            drop_player_name=claim.drop_player.full_name if claim.drop_player else None,
            priority=claim.priority,
            status=claim.status,
            created_at=claim.created_at,
            processed_at=claim.processed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting waiver claim: {str(e)}")


@router.delete("/waiver-claims/{claim_id}")
def cancel_waiver_claim(
    claim_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Cancel a pending waiver claim."""
    waiver_service = WaiverService(db)

    # For now, allow any user to cancel any claim
    # In a full implementation, you'd validate team ownership

    try:
        # Get the claim to find the team_id
        from app.models import WaiverClaim

        claim = db.query(WaiverClaim).filter(WaiverClaim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Waiver claim not found")

        success = waiver_service.cancel_claim(claim_id, claim.team_id)
        if not success:
            raise HTTPException(status_code=400, detail="Unable to cancel claim")

        return {"message": "Waiver claim cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling waiver claim: {str(e)}")


@router.get("/teams/{team_id}/waiver-priority", response_model=WaiverPriorityResponse)
def get_team_waiver_priority(
    team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> WaiverPriorityResponse:
    """Get waiver priority for a team."""
    waiver_service = WaiverService(db)

    try:
        priority = waiver_service.calculate_waiver_priority(team_id)

        return WaiverPriorityResponse(team_id=team_id, priority=priority)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waiver priority: {str(e)}")


@router.get("/leagues/{league_id}/waiver-priority", response_model=list[WaiverPriorityResponse])
def get_league_waiver_priority_order(
    league_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[WaiverPriorityResponse]:
    """Get waiver priority order for all teams in a league."""
    waiver_service = WaiverService(db)

    try:
        priority_order = waiver_service.get_waiver_priority_order(league_id)

        return [
            WaiverPriorityResponse(
                team_id=team_info["team_id"], team_name=team_info["team_name"], priority=team_info["priority"]
            )
            for team_info in priority_order
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting waiver priority order: {str(e)}")


@router.post("/admin/process-waivers")
def process_waivers(
    league_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Process all pending waiver claims (admin endpoint)."""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    waiver_service = WaiverService(db)

    try:
        results = waiver_service.process_waivers(league_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing waivers: {str(e)}")
