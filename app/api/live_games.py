"""
Live games API endpoints for real-time game updates and fantasy scoring.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.ws_manager import manager
from app.models import Team, User
from app.services.cache import CacheService
from app.services.live_games import LiveGameService

router = APIRouter(prefix="/api/v1/live", tags=["live_games"])


@router.get("/games/today")
def get_todays_live_games(
    *, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all live games for today with current status."""
    try:
        LiveGameService(db)
        cache_service = CacheService(db)

        # Check cache first
        cache_key = cache_service.create_cache_key("todays_live_games", date=datetime.utcnow().date())
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data

        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)

        from app.models import Game, LiveGameTracker

        # Get today's games with their tracking status
        games_query = db.query(Game).filter(Game.date >= today, Game.date < tomorrow).all()

        live_games = []
        for game in games_query:
            # Get live tracking data if available
            tracker = db.query(LiveGameTracker).filter(LiveGameTracker.game_id == game.id).first()

            game_data = {
                "game_id": game.id,
                "home_team": {
                    "id": game.home_team_id,
                    "name": game.home_team.name if game.home_team else "Unknown",
                    "abbreviation": game.home_team.abbreviation if game.home_team else "UNK",
                },
                "away_team": {
                    "id": game.away_team_id,
                    "name": game.away_team.name if game.away_team else "Unknown",
                    "abbreviation": game.away_team.abbreviation if game.away_team else "UNK",
                },
                "scheduled_time": game.date.isoformat(),
                "status": game.status,
                "venue": game.venue,
                "is_live_tracked": tracker is not None and tracker.is_active if tracker else False,
            }

            # Add live data if available
            if tracker:
                game_data.update(
                    {
                        "live_status": tracker.status,
                        "quarter": tracker.quarter,
                        "time_remaining": tracker.time_remaining,
                        "home_score": tracker.home_score,
                        "away_score": tracker.away_score,
                        "last_update": tracker.last_update.isoformat(),
                        "next_update": tracker.next_update.isoformat(),
                    }
                )
            else:
                game_data.update(
                    {"live_status": game.status, "home_score": game.home_score, "away_score": game.away_score}
                )

            live_games.append(game_data)

        result = {
            "date": today.isoformat(),
            "games_count": len(live_games),
            "games": live_games,
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Cache for 2 minutes
        cache_service.set(cache_key, result, ttl_seconds=120, endpoint="todays_live_games")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's live games: {str(e)}")


@router.get("/games/{game_id}")
def get_live_game_data(
    *, game_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed live data for a specific game."""
    try:
        live_game_service = LiveGameService(db)

        game_data = live_game_service.get_live_game_data(game_id)
        if not game_data:
            raise HTTPException(status_code=404, detail="Live game data not found")

        return game_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching live game data: {str(e)}")


@router.get("/teams/{team_id}/fantasy-score")
def get_live_fantasy_score(
    *, team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get live fantasy score for a team."""
    try:
        # Verify team belongs to user
        team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()

        if not team:
            raise HTTPException(status_code=404, detail="Team not found or access denied")

        live_game_service = LiveGameService(db)

        fantasy_score_data = live_game_service.get_live_fantasy_scores(team_id)
        if "error" in fantasy_score_data:
            raise HTTPException(status_code=500, detail=fantasy_score_data["error"])

        return fantasy_score_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching live fantasy score: {str(e)}")


@router.post("/games/{game_id}/start-tracking")
def start_game_tracking(
    *, game_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start live tracking for a game (admin only)."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        live_game_service = LiveGameService(db)

        if live_game_service.start_tracking_game(game_id):
            return {"success": True, "message": f"Started tracking game {game_id}", "game_id": game_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to start tracking game")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting game tracking: {str(e)}")


@router.post("/games/{game_id}/stop-tracking")
def stop_game_tracking(
    *, game_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop live tracking for a game (admin only)."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        live_game_service = LiveGameService(db)

        if live_game_service.stop_tracking_game(game_id):
            return {"success": True, "message": f"Stopped tracking game {game_id}", "game_id": game_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop tracking game")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping game tracking: {str(e)}")


@router.get("/cache/stats")
def get_cache_statistics(
    *, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get cache statistics (admin only)."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        cache_service = CacheService(db)

        # Get general cache info
        cache_info = cache_service.get_cache_info()

        # Get today's statistics
        today_stats = cache_service.get_cache_stats()

        return {
            "cache_info": cache_info,
            "daily_stats": {
                "date": today_stats.date.isoformat() if today_stats else None,
                "total_requests": today_stats.total_requests if today_stats else 0,
                "cache_hits": today_stats.cache_hits if today_stats else 0,
                "cache_misses": today_stats.cache_misses if today_stats else 0,
                "hit_rate": round(today_stats.hit_rate, 2) if today_stats else 0,
                "api_calls_saved": today_stats.api_calls_saved if today_stats else 0,
                "endpoint_stats": today_stats.endpoint_stats if today_stats else {},
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cache statistics: {str(e)}")


# WebSocket endpoints
@router.websocket("/ws/games/{game_id}")
async def websocket_live_game(websocket: WebSocket, game_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for live game updates."""
    try:
        await manager.connect_live_game(websocket, game_id)

        # Send initial game data
        live_game_service = LiveGameService(db)
        initial_data = live_game_service.get_live_game_data(game_id)
        if initial_data:
            await websocket.send_json({"event": "initial_data", "data": initial_data})

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for incoming messages (ping/pong, etc.)
                await websocket.receive_text()
                # Echo back for keep-alive
                await websocket.send_json({"event": "pong", "timestamp": datetime.utcnow().isoformat()})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_live_game(websocket, game_id)


@router.websocket("/ws/teams/{team_id}/fantasy-score")
async def websocket_live_fantasy_score(websocket: WebSocket, team_id: int, db: Session = Depends(get_db)):
    """WebSocket endpoint for live fantasy score updates."""
    try:
        await manager.connect_live_team(websocket, team_id)

        # Send initial fantasy score data
        live_game_service = LiveGameService(db)
        initial_data = live_game_service.get_live_fantasy_scores(team_id)
        if "error" not in initial_data:
            await websocket.send_json({"event": "initial_fantasy_score", "data": initial_data})

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for incoming messages (ping/pong, etc.)
                await websocket.receive_text()
                # Echo back for keep-alive
                await websocket.send_json({"event": "pong", "timestamp": datetime.utcnow().isoformat()})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_live_team(websocket, team_id)
