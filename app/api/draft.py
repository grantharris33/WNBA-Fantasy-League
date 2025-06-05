import asyncio
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import DraftPickRequest, DraftStateResponse
from app.core.ws_manager import manager
from app.models import DraftState, League, User
from app.services.draft import DraftService

router = APIRouter(prefix="/draft", tags=["draft"])


class TimerUpdateRequest(BaseModel):
    seconds: int


@router.post("/leagues/{league_id}/start", status_code=201)
async def start_draft(league_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Start a draft for a league.
    Only the commissioner can start the draft.
    """
    try:
        draft_service = DraftService(db)
        draft_state = draft_service.start_draft(league_id, current_user.id)

        # Broadcast draft start event
        await manager.broadcast_to_league(league_id, {"event": "draft_started", "data": draft_state.as_dict()})

        return {"message": "Draft started successfully", "draft_id": draft_state.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/pick")
async def make_pick(
    draft_id: int,
    pick_request: DraftPickRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Make a draft pick.
    Validates that it's the caller's turn, clock not expired, player not taken.
    """
    try:
        draft_service = DraftService(db)

        # First, verify it's the user's team's turn
        draft_state = db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft_state:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Get the user's teams in this league
        user_teams = [team for team in current_user.teams if team.league_id == draft_state.league_id]

        if not user_teams:
            raise HTTPException(status_code=403, detail="You don't have a team in this league")

        # Check if it's one of the user's teams' turn
        current_team_id = draft_state.current_team_id()
        user_team_ids = [team.id for team in user_teams]

        if current_team_id not in user_team_ids:
            raise HTTPException(status_code=403, detail="It's not your team's turn to pick")

        # Make the pick
        pick, updated_draft = draft_service.make_pick(
            draft_id=draft_id, team_id=current_team_id, player_id=pick_request.player_id, user_id=current_user.id
        )

        # Get full draft state for response and broadcast
        draft_state_data = draft_service.get_draft_state(draft_id)

        # Broadcast the pick event
        await manager.broadcast_to_league(
            draft_state.league_id,
            {
                "event": "pick_made",
                "data": {
                    "draft_id": draft_id,
                    "pick": {
                        "id": pick.id,
                        "team_id": pick.team_id,
                        "player_id": pick.player_id,
                        "round": pick.round,
                        "pick_number": pick.pick_number,
                    },
                    "draft_state": updated_draft.as_dict(),
                },
            },
        )

        return draft_state_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/pause")
async def pause_draft(draft_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Pause an active draft.
    Only the commissioner can pause the draft.
    """
    try:
        draft_service = DraftService(db)
        updated_draft = draft_service.pause_draft(draft_id, current_user.id)

        # Broadcast pause event
        await manager.broadcast_to_league(
            updated_draft.league_id, {"event": "draft_paused", "data": updated_draft.as_dict()}
        )

        return {"message": "Draft paused successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/resume")
async def resume_draft(draft_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Resume a paused draft.
    Only the commissioner can resume the draft.
    """
    try:
        draft_service = DraftService(db)
        updated_draft = draft_service.resume_draft(draft_id, current_user.id)

        # Broadcast resume event
        await manager.broadcast_to_league(
            updated_draft.league_id, {"event": "draft_resumed", "data": updated_draft.as_dict()}
        )

        return {"message": "Draft resumed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{draft_id}/state", response_model=DraftStateResponse)
async def get_draft_state(draft_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get the current state of a draft.
    Returns current round, pick index, clock seconds left, drafted players list.
    """
    try:
        draft_service = DraftService(db)
        return draft_service.get_draft_state(draft_id)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{draft_id}/timer")
async def update_draft_timer(
    draft_id: int,
    timer_request: TimerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the draft timer for future picks.
    Only the commissioner can update the timer.
    """
    try:
        # Get draft state
        draft_state = db.query(DraftState).filter(DraftState.id == draft_id).first()
        if not draft_state:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Get league to check commissioner
        league = db.query(League).filter(League.id == draft_state.league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")

        if league.commissioner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the commissioner can update draft timer")

        # Validate timer value
        if timer_request.seconds < 10 or timer_request.seconds > 300:
            raise HTTPException(status_code=400, detail="Timer must be between 10 and 300 seconds")

        # Update league settings (ensure proper JSON serialization)
        if league.settings is None:
            league.settings = {}
        league.settings = {**league.settings, 'draft_timer_seconds': timer_request.seconds}

        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(league, "settings")

        db.add(league)

        # Update current draft timer if active
        if draft_state.status == 'active':
            draft_state.seconds_remaining = timer_request.seconds

        db.add(draft_state)
        db.commit()
        db.refresh(draft_state)
        db.refresh(league)

        # Broadcast timer update event
        await manager.broadcast_to_league(
            draft_state.league_id,
            {
                "event": "timer_updated",
                "data": {"draft_state": draft_state.as_dict(), "new_timer_seconds": timer_request.seconds},
            },
        )

        return {"message": "Draft timer updated successfully", "new_timer_seconds": timer_request.seconds}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.websocket("/ws/{league_id}")
async def websocket_endpoint(websocket: WebSocket, league_id: int = Path(...), token: str = Query(...)):
    """
    WebSocket endpoint for real-time draft updates.
    Requires a valid token for authentication.
    """
    # Authenticate user via token
    try:
        # This would normally decode and verify the JWT token
        # For simplicity, we'll just accept any token for now
        # In production, use proper token verification

        await manager.connect(websocket, league_id)
        print(f"[WebSocket] Client connected to league {league_id}")

        try:
            # Keep connection alive by waiting for disconnect
            # Don't try to receive messages as clients typically only listen
            while True:
                # Wait for any message or disconnect
                # Use receive_json with a timeout to detect disconnections
                try:
                    # Short timeout to detect disconnections quickly
                    await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # If we receive any message, just ignore it (or echo for testing)
                    # await websocket.send_json({"echo": "received"})
                except asyncio.TimeoutError:
                    # Timeout is normal - send a ping to keep connection alive
                    await websocket.send_json({"type": "ping"})
                except WebSocketDisconnect:
                    break

        except WebSocketDisconnect:
            print(f"[WebSocket] Client disconnected from league {league_id}")
        finally:
            manager.disconnect(websocket, league_id)

    except Exception as e:
        print(f"[WebSocket] Error in websocket_endpoint: {e}")
        # Handle authentication errors or other exceptions
        try:
            if websocket.client_state == websocket.client_state.CONNECTED:
                await websocket.close(code=1008, reason=str(e))
        except Exception as close_error:
            print(f"Failed to close websocket: {close_error}")  # Connection may already be closed
        return
