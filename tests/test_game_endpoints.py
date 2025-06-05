from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.external_apis.rapidapi_client import RetryError, wnba_client
from app.main import app

summary_response = {
    "header": {
        "competitions": [
            {
                "id": "game123",
                "status": {"type": {"description": "Final"}},
                "venue": {"fullName": "Arena"},
                "competitors": [
                    {"id": "1", "team": {"id": "1", "abbreviation": "AAA"}, "score": "90"},
                    {"id": "2", "team": {"id": "2", "abbreviation": "BBB"}, "score": "85"},
                ],
            }
        ]
    },
    "boxscore": {
        "players": [
            {
                "team": {"id": "1"},
                "statistics": [
                    {
                        "athletes": [
                            {
                                "athlete": {"id": "p1", "displayName": "Player 1"},
                                "stats": ["0", "0", "0", "0", "0", "0", "1", "2", "0", "0", "0", "0", "0", "5"],
                            }
                        ]
                    }
                ],
            },
            {
                "team": {"id": "2"},
                "statistics": [
                    {
                        "athletes": [
                            {
                                "athlete": {"id": "p2", "displayName": "Player 2"},
                                "stats": ["0", "0", "0", "0", "0", "0", "2", "1", "0", "0", "0", "0", "0", "7"],
                            }
                        ]
                    }
                ],
            },
        ]
    },
}

play_response = {
    "header": {"competitions": [{"id": "game123"}]},
    "plays": [
        {"clock": {"displayValue": "10:00"}, "text": "Jump ball", "team": {"id": "1"}, "period": {"number": 1}},
        {
            "clock": {"displayValue": "9:55"},
            "text": "Player 1 makes shot",
            "team": {"id": "1"},
            "period": {"number": 1},
        },
    ],
}


@pytest.fixture
def client():
    return TestClient(app)


def test_game_summary_endpoint(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_game_summary", AsyncMock(return_value=summary_response))

    resp = client.get("/api/v1/games/game123/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["game"]["game_id"] == "game123"
    assert len(data["teams"]) == 2
    assert data["teams"][0]["players"][0]["player_id"] == "p1"


def test_game_playbyplay_endpoint(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_game_playbyplay", AsyncMock(return_value=play_response))

    resp = client.get("/api/v1/games/game123/playbyplay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["game_id"] == "game123"
    assert len(data["events"]) == 2


def test_game_summary_error(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_game_summary", AsyncMock(side_effect=RetryError("fail")))

    resp = client.get("/api/v1/games/bad/summary")
    assert resp.status_code == 502
