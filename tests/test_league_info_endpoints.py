from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.external_apis.rapidapi_client import RetryError, wnba_client
from app.main import app

schedule_games = [
    {
        "id": "401",
        "date": "2025-05-04T20:00Z",
        "completed": True,
        "venue": {"fullName": "Arena"},
        "competitors": [
            {"id": "1", "abbrev": "AAA", "displayName": "A Team", "isHome": True, "score": "90", "winner": True},
            {"id": "2", "abbrev": "BBB", "displayName": "B Team", "isHome": False, "score": "85", "winner": False},
        ],
    }
]

news_raw = {"articles": [{"headline": "News", "link": "http://a", "published": "2025"}]}

injuries_raw = {
    "teams": [
        {
            "id": "1",
            "name": "A Team",
            "injuries": [{"id": "p1", "name": "Player 1", "status": "out", "comment": "knee"}],
        }
    ]
}


@pytest.fixture
def client():
    return TestClient(app)


def test_schedule_endpoint(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_schedule", AsyncMock(return_value=schedule_games))
    resp = client.get("/api/v1/schedule?date=2025-05-04")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2025-05-04"
    assert len(data["games"]) == 1
    assert data["games"][0]["game_id"] == "401"


def test_news_endpoint(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_wnba_news", AsyncMock(return_value=news_raw))
    resp = client.get("/api/v1/news?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["headline"] == "News"


def test_injuries_endpoint(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_league_injuries", AsyncMock(return_value=injuries_raw))
    resp = client.get("/api/v1/injuries")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["teams"]) == 1
    assert data["teams"][0]["team_id"] == "1"


def test_schedule_error(client, monkeypatch):
    monkeypatch.setattr(wnba_client, "fetch_schedule", AsyncMock(side_effect=RetryError("fail")))
    resp = client.get("/api/v1/schedule?date=2025-05-04")
    assert resp.status_code == 502
