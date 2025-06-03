from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_jobs_route(monkeypatch, tmp_path: Path):
    """Ensure nightly job is registered and exposed via /jobs route."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("RAPIDAPI_KEY", "dummy-key")

    # Import app after env vars set
    from importlib import reload

    import app.main as main

    reload(main)  # ensure startup executed with monkeypatched env

    transport = ASGITransport(main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/jobs")
        assert resp.status_code == 200
        jobs = resp.json()
        assert any(job["id"] == "nightly_ingest" for job in jobs)


# ---------------------------------------------------------------------------
# Mocking helpers
# ---------------------------------------------------------------------------


class _StubClient:
    """Minimal awaitable client API for ingest helpers."""

    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = responses
        self.calls = 0

    async def get(self, url: str, params: dict[str, Any] | None = None):
        class _Resp:
            def __init__(self, data: dict[str, Any]):
                self._data = data
                self.status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return self._data

        response = self._responses[self.calls]
        self.calls += 1
        return _Resp(response)


@pytest.mark.asyncio
async def test_rapidapi_client_retry(monkeypatch):
    """Test that the RapidApiClient retries until success."""
    import httpx

    from app.external_apis.rapidapi_client import RapidApiClient

    class DummyResp:
        def __init__(self, ok: bool):
            self._ok = ok
            # Mock status_code for HTTPStatusError creation
            self.status_code = 500 if not ok else 200
            self.request = None  # Required for HTTPStatusError

        def raise_for_status(self):
            if not self._ok:
                # Raise HTTPStatusError which will be converted to RetryableError
                raise httpx.HTTPStatusError("Server error", request=self.request, response=self)

        def json(self):
            return {"data": "test"}

    class DummyClient:
        def __init__(self):
            self.calls = 0

        async def get(self, url, params=None):  # noqa: D401
            self.calls += 1
            if self.calls < 3:
                return DummyResp(False)
            return DummyResp(True)

    # Create a RapidApiClient with our mock client
    client = RapidApiClient(base_url="https://test.com", host="test.com")
    client._client = DummyClient()

    # Patch the retry to make tests faster
    monkeypatch.setattr("app.external_apis.rapidapi_client.wait_exponential", lambda *args, **kwargs: None)

    result = await client._get_json("test")
    assert isinstance(result, dict)
    assert client._client.calls == 3


@pytest.mark.asyncio
async def test_ingest_idempotent(monkeypatch, tmp_path: Path):
    """Running ingest twice for same date should not create duplicates."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("RAPIDAPI_KEY", "dummy-key")
    monkeypatch.setenv("TESTING", "true")

    import app.core.database as db

    db.init_db()

    from app.external_apis.rapidapi_client import wnba_client
    from app.jobs import ingest as ing

    # Prepare stub schedule (one game) and box-score payload
    schedule_payload = {"20250101": [{"id": "game1"}]}

    box_payload = {
        "players": [
            {
                "statistics": [
                    {
                        "athletes": [
                            {
                                "athlete": {"id": "1", "displayName": "Player One", "position": {"abbreviation": "G"}},
                                "stats": [
                                    "20",  # MIN
                                    "2-7",  # FG
                                    "1-1",  # 3PT
                                    "2-2",  # FT
                                    "0",  # OREB
                                    "1",  # DREB
                                    "1",  # REB
                                    "1",  # AST
                                    "1",  # STL
                                    "0",  # BLK
                                    "0",  # TO
                                    "4",  # PF
                                    "-10",  # +/-
                                    "7",  # PTS
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Mock the RapidApiClient _get_json method
    async def mock_get_json(endpoint, params=None):
        if endpoint == "wnbaschedule":
            return schedule_payload
        elif endpoint == "wnbabox":
            return box_payload
        return {}

    # Apply our mock
    monkeypatch.setattr(wnba_client, "_get_json", mock_get_json)

    # Also mock close to avoid issues in tests
    async def mock_close():
        pass

    monkeypatch.setattr(wnba_client, "close", mock_close)

    target_date = dt.date(2025, 1, 1)

    # Run twice
    await ing.ingest_stat_lines(target_date)
    await ing.ingest_stat_lines(target_date)

    from app import models as m

    session = db.SessionLocal()
    count = session.query(m.StatLine).count()
    assert count == 1
    session.close()


@pytest.mark.asyncio
async def test_update_weekly_team_scores(monkeypatch, tmp_path: Path):
    # Isolate DB
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    from app.core import database as db


def test_backfill_cli(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    # Ensure DB has tables
